# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import os
import re
import sys
import io

from argparse import ArgumentParser
from os.path import normpath
from tempfile import mkdtemp
from shutil import rmtree

from .configuration import (
    argument_parser_setup, merge_options_and_set_defaults,
    parse_config_file, parse_config_into_dict)
from .gcov import (find_existing_gcov_files, find_datafiles,
                   process_existing_gcov_file, process_datafile)
from .utils import (AlwaysMatchFilter,
                    DirectoryPrefixFilter, Logger)
from .version import __version__
from .workers import Workers

# Readers
from .reader import Readers
# Writers
from .writer import Writers
from .writer.utils import get_global_stats


#
# Exits with status 2 if below threshold
#
def fail_under(covdata, threshold_line, threshold_branch, logger):
    (lines_total, lines_covered, percent_lines,
        branches_total, branches_covered,
        percent_branches) = get_global_stats(covdata)

    if branches_total == 0:
        percent_branches = 100.0

    line_nok = False
    branch_nok = False
    if percent_lines < threshold_line:
        line_nok = True
        logger.error("failed minimum line coverage (got {}%, minimum {}%)", percent_lines, threshold_line)
    if percent_branches < threshold_branch:
        branch_nok = True
        logger.error("failed minimum branch coverage (got {}%, minimum {}%)", percent_branches, threshold_branch)
    if line_nok and branch_nok:
        sys.exit(6)
    if line_nok:
        sys.exit(2)
    if branch_nok:
        sys.exit(4)


def create_argument_parser():
    """Create the argument parser."""

    parser = ArgumentParser(add_help=False)
    parser.usage = "gcovr [options] [search_paths...]"
    parser.description = \
        "A utility to run gcov and summarize the coverage in simple reports."

    parser.epilog = "See <http://gcovr.com/> for the full manual."

    options = parser.add_argument_group('Options')
    options.add_argument(
        "-h", "--help",
        help="Show this help message, then exit.",
        action="help"
    )
    options.add_argument(
        "--version",
        help="Print the version number, then exit.",
        action="store_true",
        dest="version",
        default=False
    )

    argument_parser_setup(parser, options, Readers, Writers)

    return parser


COPYRIGHT = (
    "Copyright 2013-2018 the gcovr authors\n"
    "Copyright 2013 Sandia Corporation\n"
    "Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,\n"
    "the U.S. Government retains certain rights in this software."
)


def find_config_name(partial_options):
    cfg_name = getattr(partial_options, 'config', None)
    if cfg_name is not None:
        return cfg_name

    root = getattr(partial_options, 'root', '')
    if root:
        cfg_name = os.path.join(root, 'gcovr.cfg')
    else:
        cfg_name = 'gcovr.cfg'

    if os.path.isfile(cfg_name):
        return cfg_name

    return None


class Options(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def main(args=None):
    parser = create_argument_parser()
    cli_options = parser.parse_args(args=args)

    # load the config
    cfg_name = find_config_name(cli_options)
    cfg_options = {}
    if cfg_name is not None:
        with io.open(cfg_name, encoding='UTF-8') as cfg_file:
            cfg_options = parse_config_into_dict(
                parse_config_file(cfg_file, filename=cfg_name))

    options_dict = merge_options_and_set_defaults(
        [cfg_options, cli_options.__dict__])
    options = Options(**options_dict)

    logger = Logger(options.verbose)

    if cli_options.version:
        logger.msg(
            "gcovr {version}\n"
            "\n"
            "{copyright}",
            version=__version__, copyright=COPYRIGHT)
        sys.exit(0)

    Readers.check_options(options, logger)
    Writers.check_options(options, logger)

    if options.objdir is not None:
        if not options.objdir:
            logger.error(
                "empty --object-directory option.\n"
                "\tThis option specifies the path to the object file "
                "directory of your project.\n"
                "\tThis option cannot be an empty string.")
            sys.exit(1)
        tmp = options.objdir.replace('/', os.sep).replace('\\', os.sep)
        while os.sep + os.sep in tmp:
            tmp = tmp.replace(os.sep + os.sep, os.sep)
        if normpath(options.objdir) != tmp:
            logger.warn(
                "relative referencing in --object-directory.\n"
                "\tthis could cause strange errors when gcovr attempts to\n"
                "\tidentify the original gcc working directory.")
        if not os.path.exists(normpath(options.objdir)):
            logger.error(
                "Bad --object-directory option.\n"
                "\tThe specified directory does not exist.")
            sys.exit(1)

    options.starting_dir = os.path.abspath(os.getcwd())
    if not options.root:
        logger.error(
            "empty --root option.\n"
            "\tRoot specifies the path to the root "
            "directory of your project.\n"
            "\tThis option cannot be an empty string.")
        sys.exit(1)
    options.root_dir = os.path.abspath(options.root)

    #
    # Setup filters
    #

    # The root filter isn't technically a filter,
    # but is used to turn absolute paths into relative paths
    options.root_filter = re.compile('^' + re.escape(options.root_dir + os.sep))

    if options.exclude_dirs is not None:
        options.exclude_dirs = [
            f.build_filter(logger) for f in options.exclude_dirs]

    options.exclude = [f.build_filter(logger) for f in options.exclude]
    options.filter = [f.build_filter(logger) for f in options.filter]
    if not options.filter:
        options.filter = [DirectoryPrefixFilter(options.root_dir)]

    options.gcov_exclude = [
        f.build_filter(logger) for f in options.gcov_exclude]
    options.gcov_filter = [f.build_filter(logger) for f in options.gcov_filter]
    if not options.gcov_filter:
        options.gcov_filter = [AlwaysMatchFilter()]

    # Output the filters for debugging
    for name, filters in [
        ('--root', [options.root_filter]),
        ('--filter', options.filter),
        ('--exclude', options.exclude),
        ('--gcov-filter', options.gcov_filter),
        ('--gcov-exclude', options.gcov_exclude),
        ('--exclude-directories', options.exclude_dirs),
    ]:
        logger.verbose_msg('Filters for {}: ({})', name, len(filters))
        for f in filters:
            logger.verbose_msg('- {}', f)

    if options.exclude_lines_by_pattern:
        try:
            re.compile(options.exclude_lines_by_pattern)
        except re.error as e:
            logger.error(
                "--exclude-lines-by-pattern: "
                "Invalid regular expression: {}, error: {}",
                repr(options.exclude_lines_by_pattern), e)
            sys.exit(1)

    covdata = dict()
    Readers.read(covdata, options, logger)
    if not len(covdata.keys()):
        collect_coverage_from_gcov(covdata, options, logger)

    logger.verbose_msg("Gathered coveraged data for {} files", len(covdata))

    # Print reports
    Writers.write(covdata, options, logger)

    if options.fail_under_line > 0.0 or options.fail_under_branch > 0.0:
        fail_under(covdata, options.fail_under_line, options.fail_under_branch, logger)


def collect_coverage_from_gcov(covdata, options, logger):
    datafiles = set()

    find_files = find_datafiles
    process_file = process_datafile
    if options.gcov_files:
        find_files = find_existing_gcov_files
        process_file = process_existing_gcov_file

    # Get data files
    if not options.search_paths:
        options.search_paths = [options.root]

        if options.objdir is not None:
            options.search_paths.append(options.objdir)

    for search_path in options.search_paths:
        datafiles.update(find_files(search_path, logger, options.exclude_dirs))

    # Get coverage data
    with Workers(options.gcov_parallel, lambda: {
                 'covdata': dict(),
                 'workdir': mkdtemp(),
                 'toerase': set(),
                 'options': options}) as pool:
        logger.verbose_msg("Pool started with {} threads", pool.size())
        for file_ in datafiles:
            pool.add(process_file, file_)
        contexts = pool.wait()

    toerase = set()
    for context in contexts:
        for fname, cov in context['covdata'].items():
            if fname not in covdata:
                covdata[fname] = cov
            else:
                covdata[fname].update(cov)
        toerase.update(context['toerase'])
        rmtree(context['workdir'])
    for filepath in toerase:
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == '__main__':
    main()
