# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.1, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2022 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import logging
import os
import re
import shlex
import subprocess
import io
from threading import Lock

from .utils import search_file, commonpath
from .workers import locked_directory
from .coverage import FileCoverage
from .gcov_parser import parse_metadata, parse_coverage, ParserFlags

logger = logging.getLogger("gcovr")

output_re = re.compile(r"[Cc]reating [`'](.*)'$")
source_re = re.compile(
    r"(?:[Cc](?:annot|ould not) open (?:source|graph|output) file|: No such file or directory)"
)
unknown_cla_re = re.compile(r"Unknown command line argument")


def find_existing_gcov_files(search_path, exclude_dirs):
    """Find .gcov files under the given search path."""
    logger.debug(f"Scanning directory {search_path} for gcov files...")
    gcov_files = list(
        search_file(
            re.compile(r".*\.gcov$").match, search_path, exclude_dirs=exclude_dirs
        )
    )
    logger.debug(f"Found {len(gcov_files)} files (and will process all of them)")
    return gcov_files


def find_datafiles(search_path, exclude_dirs):
    """Find .gcda and .gcno files under the given search path.

    The .gcno files will *only* produce uncovered results.
    However, that is useful information when a compilation unit
    is never actually exercised by the test code.
    So we ONLY return them if there's no corresponding .gcda file.
    """
    logger.debug(f"Scanning directory {search_path} for gcda/gcno files...")
    files = list(
        search_file(
            re.compile(r".*\.gc(da|no)$").match, search_path, exclude_dirs=exclude_dirs
        )
    )
    gcda_files = []
    gcno_files = []
    known_file_stems = set()
    for filename in files:
        stem, ext = os.path.splitext(filename)
        if ext == ".gcda":
            gcda_files.append(filename)
            known_file_stems.add(stem)
        elif ext == ".gcno":
            gcno_files.append(filename)
    # remove gcno files that match a gcno stem
    gcno_files = [
        filename
        for filename in gcno_files
        if os.path.splitext(filename)[0] not in known_file_stems
    ]
    logger.debug(
        f"Found {len(files)} files (and will process {len(gcda_files) + len(gcno_files)})"
    )
    return gcda_files + gcno_files


#
# Process a single gcov datafile
#
def process_gcov_data(data_fname, covdata, source_fname, options, currdir=None):
    with io.open(
        data_fname, "r", encoding=options.source_encoding, errors="replace"
    ) as INPUT:
        lines = INPUT.read().splitlines()

    # Find the source file
    # TODO: instead of heuristics, use "working directory" if available
    metadata = parse_metadata(lines)
    fname = guess_source_file_name(
        metadata["Source"].strip(),
        data_fname,
        source_fname,
        root_dir=options.root_dir,
        starting_dir=options.starting_dir,
        obj_dir=None if options.objdir is None else os.path.abspath(options.objdir),
        currdir=currdir,
    )

    logger.debug(f"Parsing coverage data for file {fname}")

    # Return if the filename does not match the filter
    # Return if the filename matches the exclude pattern
    filtered, excluded = apply_filter_include_exclude(
        fname, options.filter, options.exclude
    )

    if filtered:
        logger.debug(f"  Filtering coverage data for file {fname}")
        return

    if excluded:
        logger.debug(f"  Excluding coverage data for file {fname}")
        return

    key = os.path.normpath(fname)

    parser_flags = ParserFlags.NONE
    if options.gcov_ignore_parse_errors:
        parser_flags |= ParserFlags.IGNORE_PARSE_ERRORS
    if options.exclude_function_lines:
        parser_flags |= ParserFlags.EXCLUDE_FUNCTION_LINES
    if options.exclude_internal_functions:
        parser_flags |= ParserFlags.EXCLUDE_INTERNAL_FUNCTIONS
    if options.exclude_unreachable_branches:
        parser_flags |= ParserFlags.EXCLUDE_UNREACHABLE_BRANCHES
    if options.exclude_throw_branches:
        parser_flags |= ParserFlags.EXCLUDE_THROW_BRANCHES
    if options.respect_exclusion_markers:
        parser_flags |= ParserFlags.RESPECT_EXCLUSION_MARKERS
    if options.show_decision:
        parser_flags |= ParserFlags.PARSE_DECISIONS

    coverage = parse_coverage(
        lines,
        filename=key,
        exclude_lines_by_pattern=options.exclude_lines_by_pattern,
        exclude_pattern_prefix=options.exclude_pattern_prefix,
        flags=parser_flags,
    )
    covdata.setdefault(key, FileCoverage(key)).update(coverage)


def guess_source_file_name(
    gcovname,
    data_fname,
    source_fname,
    root_dir,
    starting_dir,
    obj_dir,
    currdir=None,
):
    if currdir is None:
        currdir = os.getcwd()
    if source_fname is None:
        fname = guess_source_file_name_via_aliases(gcovname, currdir, data_fname)
    else:
        fname = guess_source_file_name_heuristics(
            gcovname, currdir, root_dir, starting_dir, obj_dir, source_fname
        )

    logger.debug(
        f"Finding source file corresponding to a gcov data file\n"
        f"  currdir      {currdir}\n"
        f"  gcov_fname   {data_fname}\n"
        f"  source_fname {source_fname}\n"
        f"  root         {root_dir}\n"
        # f"  common_dir   {common_dir}\n"
        # f"  subdir       {subdir}\n"
        f"  fname        {fname}"
    )

    return fname


def guess_source_file_name_via_aliases(gcovname, currdir, data_fname):
    common_dir = commonpath([data_fname, currdir])
    fname = os.path.abspath(os.path.join(common_dir, gcovname))
    if os.path.exists(fname):
        return fname

    initial_fname = fname

    data_fname_dir = os.path.dirname(data_fname)
    fname = os.path.abspath(os.path.join(data_fname_dir, gcovname))
    if os.path.exists(fname):
        return fname

    # @latk-2018: The original code is *very* insistent
    # on returning the inital guess. Why?
    return initial_fname


def guess_source_file_name_heuristics(
    gcovname, currdir, root_dir, starting_dir, obj_dir, source_fname
):

    # gcov writes filenames with '/' path seperators even if the OS
    # separator is different, so we replace it with the correct separator
    gcovname = gcovname.replace("/", os.sep)

    # 0. Try using the current working directory as the source directory
    fname = os.path.join(currdir, gcovname)
    if os.path.exists(fname):
        return fname

    # 1. Try using the path to common prefix with the root_dir as the source directory
    fname = os.path.join(root_dir, gcovname)
    if os.path.exists(fname):
        return fname

    # 2. Try using the starting directory as the source directory
    fname = os.path.join(starting_dir, gcovname)
    if os.path.exists(fname):
        return fname

    # 3. Try using relative path from object dir
    if obj_dir is not None:
        fname = os.path.normpath(os.path.join(obj_dir, gcovname))
        if os.path.exists(fname):
            return fname

    # Get path of gcda file
    source_fname_dir = os.path.dirname(source_fname)

    # 4. Try using the path to the gcda as the source directory
    fname = os.path.join(source_fname_dir, gcovname)
    if os.path.exists(fname):
        return os.path.normpath(fname)

    # 5. Try using the path to the gcda file as the source directory, removing the path part from the gcov file
    fname = os.path.join(source_fname_dir, os.path.basename(gcovname))
    return fname


def process_datafile(filename, covdata, options, toerase):
    r"""Run gcovr in a suitable directory to collect coverage from gcda files.

    Params:
        filename (path): the path to a gcda or gcno file
        covdata (dict, mutable): the global covdata dictionary
        options (object): the configuration options namespace
        toerase (set, mutable): files that should be deleted later
        workdir (path or None): the per-thread work directory

    Returns:
        Nothing.

    Finding a suitable working directory is tricky.
    The coverage files (gcda and gcno) are stored next to object (.o) files.
    However, gcov needs to also resolve the source file name.
    The relative source file paths in the coverage data
    are relative to the gcc working directory.
    Therefore, gcov must be invoked in the same directory as gcc.
    How to find that directory? By various heuristics.

    This is complicated by the problem that the build process tells gcc
    where to run, where the sources are, and where to put the object files.
    We only know the object files and have to work everything out in reverse.

    If present, the *workdir* argument is always tried first.

    Ideally, the build process only runs gcc from *one* directory
    and the user can provide this directory as the ``--object-directory``.
    If it exists, we try that path as a workdir,
    If the path is relative,
    it is resolved relative to the gcovr cwd and the object file location.

    We next try the ``--root`` directory.
    TODO: should probably also be the gcovr start directory.

    If none of those work, we assume that
    the object files are in a subdirectory of the gcc working directory,
    i.e. we can walk the directory tree upwards.

    All of this works fine unless gcc was invoked like ``gcc -o ../path``,
    i.e. the object files are in a sibling directory.
    TODO: So far there is no good way to address this case.
    """
    logger.debug(f"Processing file: {filename}")

    abs_filename = os.path.abspath(filename)

    errors = []

    potential_wd = []

    if options.objdir:
        potential_wd = find_potential_working_directories_via_objdir(
            abs_filename, options.objdir, error=errors.append
        )

    # no objdir was specified or objdir didn't exist
    consider_parent_directories = not potential_wd

    # Always add the root directory
    potential_wd.append(options.root_dir)

    if consider_parent_directories:
        wd = os.path.dirname(abs_filename)
        while wd != potential_wd[-1]:
            potential_wd.append(wd)
            wd = os.path.dirname(wd)

    for wd in potential_wd:
        done = run_gcov_and_process_files(
            abs_filename,
            covdata,
            options=options,
            toerase=toerase,
            error=errors.append,
            chdir=wd,
        )

        if options.delete:
            if not abs_filename.endswith("gcno"):
                toerase.add(abs_filename)

        if done:
            return

    errors_output = "\n\t".join(errors)
    logger.warning(
        f"GCOV produced the following errors processing {filename}:\n"
        f"\t{errors_output}\n"
        "\t(gcovr could not infer a working directory that resolved it.)"
    )


def find_potential_working_directories_via_objdir(abs_filename, objdir, error):
    # absolute path - just return the objdir
    if os.path.isabs(objdir):
        if os.path.isdir(objdir):
            return [objdir]

    # relative path: check relative to both the cwd and the gcda file
    else:
        potential_wd = [
            testdir
            for prefix in [os.path.dirname(abs_filename), os.getcwd()]
            for testdir in [os.path.join(prefix, objdir)]
            if os.path.isdir(testdir)
        ]

        if potential_wd:
            return potential_wd

    error(
        "ERROR: cannot identify the location where GCC "
        "was run using --object-directory=%s\n" % objdir
    )

    return []


class gcov:
    __lock = Lock()
    __cmd = None
    __cmd_split = None
    __default_options = []
    __help_output = None

    def __init__(self, cmd):
        gcov.__lock.acquire()
        if gcov.__cmd is None:
            gcov.__cmd = cmd
            # If the first element of cmd - the executable name - has embedded spaces
            # (other than within quotes), it probably includes extra arguments.
            gcov.__cmd_split = shlex.split(cmd)
            gcov.__default_options = [
                "--branch-counts",
                "--branch-probabilities",
            ]

            if self.__check_gcov_option("--demangled-names"):
                gcov.__default_options.append("--demangled-names")

            if self.__check_gcov_option("--hash-filenames"):
                gcov.__default_options.append("--hash-filenames")
            elif self.__check_gcov_option("--preserve-paths"):
                gcov.__default_options.append("--preserve-paths")
            else:
                logger.warning(
                    "Options '--hash-filenames' and '--preserve-paths' are not "
                    f"supported by '{cmd}'. Source files with identical file names "
                    "may result in incorrect coverage."
                )
            gcov.__lock.release()
        else:
            gcov.__lock.release()
            assert (
                gcov.__cmd == cmd
            ), f"Gcov command must not me changed, expected '{gcov.__cmd}', got '{cmd}'"

    def __get_help_output(self):
        if gcov.__help_output is None:
            gcov.__help_output = ""
            for help_option in ["--help", "--help-hidden"]:
                gcov_process = self.run_with_args(
                    [help_option],
                    universal_newlines=True,
                )
                out, _ = gcov_process.communicate(timeout=30)

                if not gcov_process.returncode:
                    # gcov execution was successful, help argument is not supported.
                    gcov.__help_output += out
            if gcov.__help_output == "":
                # gcov tossed errors: throw exception
                raise RuntimeError("Error in gcov command line, couldn't get help.")

        return gcov.__help_output

    def __check_gcov_option(self, option):
        if option in self.__get_help_output():
            return True

        return False

    def get_default_options(self):
        return gcov.__default_options

    def run_with_args(self, args, **kwargs):
        # NB: Currently, we will only parse English output
        env = kwargs.pop("env") if "env" in kwargs else dict(os.environ)
        env["LC_ALL"] = "C"
        env["LANGUAGE"] = "en_US"

        if "cwd" not in kwargs:
            kwargs["cwd"] = "."
        cmd = gcov.__cmd_split + args
        logger.debug(f"Running gcov: '{' '.join(cmd)}' in '{kwargs['cwd']}'")

        return subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            **kwargs,
        )


def run_gcov_and_process_files(abs_filename, covdata, options, error, toerase, chdir):
    gcov_cmd = gcov(options.gcov_cmd)

    # ATTENTION:
    # This lock is essential for parallel processing because without
    # this there can be name collisions for the generated output files.
    with locked_directory(chdir):
        out, err = gcov_cmd.run_with_args(
            [
                abs_filename,
                *gcov_cmd.get_default_options(),
                "--object-directory",
                os.path.dirname(abs_filename),
            ],
            cwd=chdir,
        ).communicate()

        # find the files that gcov created
        active_gcov_files, all_gcov_files = select_gcov_files_from_stdout(
            out,
            gcov_filter=options.gcov_filter,
            gcov_exclude=options.gcov_exclude,
            chdir=chdir,
        )

    if unknown_cla_re.search(err):
        # gcov tossed errors: throw exception
        raise RuntimeError("Error in gcov command line: {}".format(err))
    elif source_re.search(err):
        # gcov tossed errors: try the next potential_wd
        error(err)
        done = False
    else:
        # Process *.gcov files
        for fname in active_gcov_files:
            process_gcov_data(fname, covdata, abs_filename, options)
        done = True

    if not options.keep:
        toerase.update(all_gcov_files)

    return done


def select_gcov_files_from_stdout(out, gcov_filter, gcov_exclude, chdir):
    active_files = []
    all_files = []

    for line in out.splitlines():
        found = output_re.search(line.strip())
        if found is None:
            continue

        fname = found.group(1)
        full = os.path.join(chdir, fname)
        all_files.append(full)

        filtered, excluded = apply_filter_include_exclude(
            fname, gcov_filter, gcov_exclude
        )

        if filtered:
            logger.debug(f"Filtering gcov file {fname}")
            continue

        if excluded:
            logger.debug(f"Excluding gcov file {fname}")
            continue

        active_files.append(full)

    return active_files, all_files


#
#  Process Already existing gcov files
#
def process_existing_gcov_file(filename, covdata, options, toerase):
    filtered, excluded = apply_filter_include_exclude(
        filename, options.gcov_filter, options.gcov_exclude
    )

    if filtered:
        logger.debug(f"This gcov file does not match the filter: {filename}")
        return

    if excluded:
        logger.debug(f"Excluding gcov file: {filename}")
        return

    process_gcov_data(filename, covdata, None, options)

    if not options.keep:
        toerase.add(filename)


def apply_filter_include_exclude(filename, include_filters, exclude_filters):
    """Apply inclusion/exclusion filters to filename

    The include_filters are tested against
    the given (relative) filename.
    The exclude_filters are tested against
    the stripped, given (relative), and absolute filenames.

    filename (str): the file path to match, should be relative
    include_filters (list of regex): ANY of these filters must match
    exclude_filters (list of regex): NONE of these filters must match

    returns: (filtered, exclude)
        filtered (bool): True when filename failed the include_filter
        excluded (bool): True when filename failed the exclude_filters
    """

    filtered = not any(f.match(filename) for f in include_filters)
    excluded = False

    if filtered:
        return filtered, excluded

    excluded = any(f.match(filename) for f in exclude_filters)

    return filtered, excluded
