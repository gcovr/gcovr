# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2022 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import logging
import os
import re
import sys
import io

from argparse import ArgumentParser
from os.path import normpath
from glob import glob
from typing import Callable, List, Optional, Tuple

from .configuration import (
    argument_parser_setup,
    merge_options_and_set_defaults,
    parse_config_file,
    parse_config_into_dict,
    OutputOrDefault,
)
from .gcov import (
    find_existing_gcov_files,
    find_datafiles,
    process_existing_gcov_file,
    process_datafile,
)
from .utils import (
    AlwaysMatchFilter,
    DirectoryPrefixFilter,
    configure_logging,
)
from .version import __version__
from .workers import Workers
from .coverage import CovData, SummarizedStats
from .merging import merge_covdata

# generators
from .writer.json import gcovr_json_files_to_coverage
from .writer.cobertura import print_cobertura_report
from .writer.html import print_html_report
from .writer.json import print_json_report, print_json_summary_report
from .writer.txt import print_text_report
from .writer.csv import print_csv_report
from .writer.summary import print_summary
from .writer.sonarqube import print_sonarqube_report
from .writer.coveralls import print_coveralls_report


logger = logging.getLogger("gcovr")


#
# Exits with status 2 if below threshold
#
def fail_under(covdata: CovData, threshold_line, threshold_branch):
    stats = SummarizedStats.from_covdata(covdata)

    # If there are no lines, mark as uncovered
    # (indicates no data at all, likely an error).
    percent_lines = stats.line.percent_or(0.0)

    # Allow data with no branches.
    percent_branches = stats.branch.percent_or(100.0)

    line_nok = False
    branch_nok = False
    if percent_lines < threshold_line:
        line_nok = True
        logger.error(
            f"failed minimum line coverage (got {percent_lines}%, minimum {threshold_line}%)"
        )
    if percent_branches < threshold_branch:
        branch_nok = True
        logger.error(
            f"failed minimum branch coverage (got {percent_branches}%, minimum {threshold_branch}%)"
        )
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
    parser.description = (
        "A utility to run gcov and summarize the coverage in simple reports."
    )

    parser.epilog = "See <http://gcovr.com/> for the full manual."

    options = parser.add_argument_group("Options")
    options.add_argument(
        "-h", "--help", help="Show this help message, then exit.", action="help"
    )
    options.add_argument(
        "--version",
        help="Print the version number, then exit.",
        action="store_true",
        dest="version",
        default=False,
    )

    argument_parser_setup(parser, options)

    return parser


COPYRIGHT = (
    "Copyright (c) 2013-2022 the gcovr authors\n"
    "Copyright (c) 2013 Sandia Corporation.\n"
    "Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,\n"
    "the U.S. Government retains certain rights in this software.\n"
)


def find_config_name(partial_options):
    cfg_name = getattr(partial_options, "config", None)
    if cfg_name is not None:
        return cfg_name

    root = getattr(partial_options, "root", "")
    if root:
        cfg_name = os.path.join(root, "gcovr.cfg")
    else:
        cfg_name = "gcovr.cfg"

    if os.path.isfile(cfg_name):
        return cfg_name

    return None


class Options(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def main(args=None):
    configure_logging()
    parser = create_argument_parser()
    cli_options = parser.parse_args(args=args)

    # load the config
    cfg_name = find_config_name(cli_options)
    cfg_options = {}
    if cfg_name is not None:
        with io.open(cfg_name, encoding="UTF-8") as cfg_file:
            cfg_options = parse_config_into_dict(
                parse_config_file(cfg_file, filename=cfg_name)
            )

    options_dict = merge_options_and_set_defaults([cfg_options, cli_options.__dict__])
    options = Options(**options_dict)

    if options.verbose:
        logger.setLevel(logging.DEBUG)

    if cli_options.version:
        sys.stdout.write(f"gcovr {__version__}\n\n{COPYRIGHT}")
        sys.exit(0)

    if options.html_title == "":
        logger.error("an empty --html_title= is not allowed.")
        sys.exit(1)

    for postfix in ["", "line", "branch"]:
        key_medium = "html_medium_threshold"
        key_high = "html_high_threshold"
        if postfix:
            key_medium += f"_{postfix}"
            key_high += f"_{postfix}"
        option_medium = f"--{key_medium.replace('_', '-')}"
        option_high = f"--{key_high.replace('_', '-')}"

        if getattr(options, key_medium) == 0:
            logger.error(f"value of {option_medium}= should not be zero.")
            sys.exit(1)

        # Inherit the defaults from the global covarage values if not set
        if postfix:
            if getattr(options, key_medium) is None:
                setattr(
                    options,
                    key_medium,
                    options.html_medium_threshold,
                )
                # To get the correct option in the error message below.
                option_medium = "--html-medium-threshold"
            if getattr(options, key_high) is None:
                setattr(
                    options,
                    key_high,
                    options.html_high_threshold,
                )
                # To get the correct option in the error message below.
                option_medium = "--html-high-threshold"

        if getattr(options, key_medium) > getattr(options, key_high):
            logger.error(
                f"value of {option_medium}={getattr(options, key_medium)} should be\n"
                f"lower than or equal to the value of {option_high}={getattr(options, key_high)}."
            )
            sys.exit(1)

    if options.html_tab_size < 1:
        logger.error("value of --html-tab-size= should be greater 0.")
        sys.exit(1)

    potential_html_output = (
        (options.html and options.html.value)
        or (options.html_details and options.html_details.value)
        or (options.output and options.output.value)
    )
    if options.html_details and not potential_html_output:
        logger.error(
            "a named output must be given, if the option --html-details\n" "is used."
        )
        sys.exit(1)

    if options.html_self_contained is False and not potential_html_output:
        logger.error(
            "can only disable --html-self-contained when a named output is given."
        )
        sys.exit(1)

    if options.objdir is not None:
        if not os.path.exists(options.objdir):
            logger.error(
                "Bad --object-directory option.\n"
                "\tThe specified directory does not exist."
            )
            sys.exit(1)

    options.starting_dir = os.path.abspath(os.getcwd())
    options.root_dir = os.path.abspath(options.root)

    #
    # Setup filters
    #

    # The root filter isn't technically a filter,
    # but is used to turn absolute paths into relative paths
    options.root_filter = re.compile("^" + re.escape(options.root_dir + os.sep))

    if options.exclude_dirs is not None:
        options.exclude_dirs = [f.build_filter() for f in options.exclude_dirs]

    options.exclude = [f.build_filter() for f in options.exclude]
    options.filter = [f.build_filter() for f in options.filter]
    if not options.filter:
        options.filter = [DirectoryPrefixFilter(options.root_dir)]

    options.gcov_exclude = [f.build_filter() for f in options.gcov_exclude]
    options.gcov_filter = [f.build_filter() for f in options.gcov_filter]
    if not options.gcov_filter:
        options.gcov_filter = [AlwaysMatchFilter()]

    # Output the filters for debugging
    for name, filters in [
        ("--root", [options.root_filter]),
        ("--filter", options.filter),
        ("--exclude", options.exclude),
        ("--gcov-filter", options.gcov_filter),
        ("--gcov-exclude", options.gcov_exclude),
        ("--exclude-directories", options.exclude_dirs),
    ]:
        logger.debug(f"Filters for {name}: ({len(filters)})")
        for f in filters:
            logger.debug(f" - {f}")

    if options.exclude_lines_by_pattern:
        try:
            re.compile(options.exclude_lines_by_pattern)
        except re.error as e:
            logger.error(
                "--exclude-lines-by-pattern: "
                f"Invalid regular expression: {repr(options.exclude_lines_by_pattern)}, error: {e}"
            )
            sys.exit(1)

    if options.exclude_branches_by_pattern:
        try:
            re.compile(options.exclude_branches_by_pattern)
        except re.error as e:
            logger.error(
                "--exclude-branches-by-pattern: "
                f"Invalid regular expression: {repr(options.exclude_branches_by_pattern)}, error: {e}"
            )
            sys.exit(1)

    covdata: CovData
    if options.add_tracefile:
        covdata = collect_coverage_from_tracefiles(options)
    else:
        covdata = collect_coverage_from_gcov(options)

    logger.debug(f"Gathered coveraged data for {len(covdata)} files")

    # Print reports
    error_occurred = print_reports(covdata, options)
    if error_occurred:
        logger.error("Error occurred while printing reports")
        sys.exit(7)

    if options.fail_under_line > 0.0 or options.fail_under_branch > 0.0:
        fail_under(covdata, options.fail_under_line, options.fail_under_branch)


def collect_coverage_from_tracefiles(options) -> CovData:
    datafiles = set()

    for trace_files_regex in options.add_tracefile:
        trace_files = glob(trace_files_regex, recursive=True)
        if not trace_files:
            logger.error(
                "Bad --add-tracefile option.\n" "\tThe specified file does not exist."
            )
            sys.exit(1)
        else:
            for trace_file in trace_files:
                datafiles.add(normpath(trace_file))

    options.root_dir = os.path.abspath(options.root)
    return gcovr_json_files_to_coverage(datafiles, options)


def collect_coverage_from_gcov(options) -> CovData:
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
        datafiles.update(find_files(search_path, options.exclude_dirs))

    # Get coverage data
    with Workers(
        options.gcov_parallel,
        lambda: {"covdata": dict(), "toerase": set(), "options": options},
    ) as pool:
        logger.debug(f"Pool started with {pool.size()} threads")
        for file_ in datafiles:
            pool.add(process_file, file_)
        contexts = pool.wait()

    toerase = set()
    covdata = dict()
    for context in contexts:
        covdata = merge_covdata(covdata, context["covdata"])
        toerase.update(context["toerase"])

    for filepath in toerase:
        if os.path.exists(filepath):
            os.remove(filepath)

    return covdata


def print_reports(covdata: CovData, options):
    Generator = Tuple[
        List[Optional[OutputOrDefault]],
        Callable[[CovData, str, Options], None],
        Callable[[], None],
    ]
    generators: List[Generator] = []

    if options.txt:
        generators.append(
            (
                [options.txt],
                print_text_report,
                lambda: logger.warning(
                    "Text output skipped - "
                    "consider providing an output file with `--txt=OUTPUT`."
                ),
            )
        )

    if options.cobertura or options.cobertura_pretty:
        generators.append(
            (
                [options.cobertura],
                print_cobertura_report,
                lambda: logger.warning(
                    "Cobertura output skipped - "
                    "consider providing an output file with `--cobertura=OUTPUT`."
                ),
            )
        )

    if options.html or options.html_details:
        generators.append(
            (
                [options.html, options.html_details],
                print_html_report,
                lambda: logger.warning(
                    "HTML output skipped - "
                    "consider providing an output file with `--html=OUTPUT`."
                ),
            )
        )

    if options.sonarqube:
        generators.append(
            (
                [options.sonarqube],
                print_sonarqube_report,
                lambda: logger.warning(
                    "Sonarqube output skipped - "
                    "consider providing an output file with `--sonarqube=OUTPUT`."
                ),
            )
        )

    if options.json or options.json_pretty:
        generators.append(
            (
                [options.json],
                print_json_report,
                lambda: logger.warning(
                    "JSON output skipped - "
                    "consider providing an output file with `--json=OUTPUT`."
                ),
            )
        )

    if options.json_summary or options.json_summary_pretty:
        generators.append(
            (
                [options.json_summary],
                print_json_summary_report,
                lambda: logger.warning(
                    "JSON summary output skipped - "
                    "consider providing an output file with `--json-summary=OUTPUT`."
                ),
            )
        )

    if options.csv:
        generators.append(
            (
                [options.csv],
                print_csv_report,
                lambda: logger.warning(
                    "CSV output skipped - "
                    "consider providing an output file with `--csv=OUTPUT`."
                ),
            )
        )

    if options.coveralls or options.coveralls_pretty:
        generators.append(
            (
                [options.coveralls],
                print_coveralls_report,
                lambda: logger.warning(
                    "Coveralls output skipped - "
                    "consider providing an output file with `--coveralls=OUTPUT`."
                ),
            )
        )

    generator_error_occurred = False
    reports_were_written = False
    default_output_used = False
    default_output = OutputOrDefault(None) if options.output is None else options.output

    for output_choices, generator, on_no_output in generators:
        output = OutputOrDefault.choose(output_choices, default=default_output)
        if output is not None and output is default_output:
            default_output_used = True
            if not output.is_dir:
                default_output = None
        if output is not None:
            if generator(covdata, output.abspath, options):
                generator_error_occurred = True
            reports_were_written = True
        else:
            on_no_output()

    if not reports_were_written:
        print_text_report(
            covdata, "-" if default_output is None else default_output.abspath, options
        )
        default_output = None

    if (
        default_output is not None
        and default_output.value is not None
        and not default_output_used
    ):
        logger.warning(
            f"--output={repr(default_output.value)} option was provided but not used."
        )

    if options.print_summary:
        print_summary(covdata)

    return generator_error_occurred


if __name__ == "__main__":
    main()
