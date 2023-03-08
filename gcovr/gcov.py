# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
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
import shlex
import subprocess
import io
from threading import Lock
from typing import Optional

from .utils import search_file, commonpath, is_fs_case_insensitive, fix_case_of_path
from .workers import locked_directory
from .gcov_parser import parse_metadata, parse_coverage
from .coverage import CovData
from .merging import get_merge_mode_from_options, insert_file_coverage
from .exclusions import apply_all_exclusions
from .decision_analysis import DecisionParser


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
def process_gcov_data(
    data_fname: str, covdata: CovData, gcda_fname: Optional[str], options, currdir=None
) -> None:
    with io.open(
        data_fname, "r", encoding=options.source_encoding, errors="replace"
    ) as INPUT:
        lines = INPUT.read().splitlines()

    # Find the source file
    # TODO: instead of heuristics, use "working directory" if available
    metadata = parse_metadata(lines)
    source = metadata.get("Source")
    if source is None:
        raise RuntimeError("Unexpected value 'None' for metadata 'Source'.")
    fname = guess_source_file_name(
        source,
        data_fname,
        gcda_fname,
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

    coverage, source_lines = parse_coverage(
        lines,
        filename=key,
        ignore_parse_errors=options.gcov_ignore_parse_errors,
    )

    apply_all_exclusions(coverage, lines=source_lines, options=options)

    if options.show_decision:
        decision_parser = DecisionParser(coverage, source_lines)
        decision_parser.parse_all_lines()

    insert_file_coverage(covdata, coverage, get_merge_mode_from_options(options))


def guess_source_file_name(
    gcovname, data_fname, gcda_fname, root_dir, starting_dir, obj_dir, currdir=None
):
    if currdir is None:
        currdir = os.getcwd()
    if gcda_fname is None:
        fname = guess_source_file_name_via_aliases(gcovname, currdir, data_fname)
    else:
        fname = guess_source_file_name_heuristics(
            gcovname, data_fname, currdir, root_dir, starting_dir, obj_dir, gcda_fname
        )

    if is_fs_case_insensitive():
        fname = fix_case_of_path(fname)

    logger.debug(
        f"Finding source file corresponding to a gcov data file\n"
        f"  gcov_fname   {data_fname}\n"
        f"  currdir      {currdir}\n"
        f"  root         {root_dir}\n"
        f"  starting_dir {starting_dir}\n"
        f"  obj_dir      {obj_dir}\n"
        f"  gcda_fname   {gcda_fname}\n"
        f"  --> fname    {fname}"
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
    gcovname, data_fname, currdir, root_dir, starting_dir, obj_dir, gcda_fname
):

    # gcov writes filenames with '/' path seperators even if the OS
    # separator is different, so we replace it with the correct separator
    gcovname = gcovname.replace("/", os.sep)

    # 0. Try using the path to the gcov file
    fname = os.path.join(os.path.dirname(data_fname), gcovname)
    if os.path.exists(fname):
        return fname

    logger.debug("Fallback to heuristic of gcovr 5.1")

    # 1. Try using the current working directory as the source directory
    fname = os.path.join(currdir, gcovname)
    if os.path.exists(fname):
        return fname

    # 2. Try using the path to common prefix with the root_dir as the source directory
    fname = os.path.join(root_dir, gcovname)
    if os.path.exists(fname):
        return fname

    # 3. Try using the starting directory as the source directory
    fname = os.path.join(starting_dir, gcovname)
    if os.path.exists(fname):
        return fname

    # 4. Try using relative path from object dir
    if obj_dir is not None:
        fname = os.path.normpath(os.path.join(obj_dir, gcovname))
        if os.path.exists(fname):
            return fname

    # Get path of gcda file
    gcda_fname_dir = os.path.dirname(gcda_fname)

    # 5. Try using the path to the gcda as the source directory
    fname = os.path.join(gcda_fname_dir, gcovname)
    if os.path.exists(fname):
        return os.path.normpath(fname)

    # 6. Try using the path to the gcda file as the source directory, removing the path part from the gcov file
    fname = os.path.join(gcda_fname_dir, os.path.basename(gcovname))
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

    abs_filename = os.path.abspath(filename).replace(
        os.path.sep, "/"
    )  # gcov requires posix style path

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
            error=errors.append,
            chdir=wd,
        )

        if options.delete:
            if not abs_filename.endswith("gcno"):
                toerase.add(abs_filename)

        if done:
            return

    errors_output = "\n\t".join(errors)
    errors_output = (
        f"GCOV produced the following errors processing {filename}:\n"
        f"\t{errors_output}\n"
        "\t(gcovr could not infer a working directory that resolved it.)\n"
        "To ignore this error use option --gcov-ignore-errors=no_working_dir_found."
    )
    logger.error(errors_output)

    # Check if error shall be ignored
    if options.gcov_ignore_errors is None or not any(
        [v in options.gcov_ignore_errors for v in ["all", "no_working_dir_found"]]
    ):
        raise RuntimeError(errors_output)


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


class GcovProgram:
    __lock = Lock()
    __cmd = None
    __cmd_split = None
    __default_options = []
    __help_output = None

    class LockContext(object):
        def __init__(self, lock: Lock):
            self.lock = lock

        def __enter__(self):
            self.lock.acquire()

        def __exit__(self, *_):
            self.lock.release()

    def __init__(self, cmd):
        with GcovProgram.LockContext(GcovProgram.__lock):
            if GcovProgram.__cmd is None:
                GcovProgram.__cmd = cmd
                # If the first element of cmd - the executable name - has embedded spaces
                # (other than within quotes), it probably includes extra arguments.
                GcovProgram.__cmd_split = shlex.split(GcovProgram.__cmd)
            else:
                assert (
                    GcovProgram.__cmd == cmd
                ), f"Gcov command must not be changed, expected '{GcovProgram.__cmd}', got '{cmd}'"

    def identify_and_cache_capabilities(self):
        with GcovProgram.LockContext(GcovProgram.__lock):
            if not GcovProgram.__default_options:
                GcovProgram.__default_options = [
                    "--branch-counts",
                    "--branch-probabilities",
                ]

                if self.__check_gcov_option("--demangled-names"):
                    GcovProgram.__default_options.append("--demangled-names")

                if self.__check_gcov_option("--hash-filenames"):
                    GcovProgram.__default_options.append("--hash-filenames")
                elif self.__check_gcov_option("--preserve-paths"):
                    GcovProgram.__default_options.append("--preserve-paths")
                else:
                    logger.warning(
                        "Options '--hash-filenames' and '--preserve-paths' are not "
                        f"supported by '{GcovProgram.__cmd}'. Source files with "
                        "identical file names may result in incorrect coverage."
                    )

    def __get_help_output(self):
        if GcovProgram.__help_output is None:
            GcovProgram.__help_output = ""
            for help_option in ["--help", "--help-hidden"]:
                gcov_process = self.__get_gcov_process(
                    [help_option],
                    universal_newlines=True,
                )
                out, _ = gcov_process.communicate(timeout=30)

                if not gcov_process.returncode:
                    # gcov execution was successful, help argument is not supported.
                    GcovProgram.__help_output += out
            if GcovProgram.__help_output == "":
                # gcov tossed errors: throw exception
                raise RuntimeError("Error in gcov command line, couldn't get help.")

        return GcovProgram.__help_output

    def __check_gcov_option(self, option):
        if option in self.__get_help_output():
            return True

        return False

    def get_default_options(self):
        return GcovProgram.__default_options

    def __get_gcov_process(self, args, **kwargs):
        # NB: Currently, we will only parse English output
        env = kwargs.pop("env") if "env" in kwargs else dict(os.environ)
        env["LC_ALL"] = "C"
        env["LANGUAGE"] = "en_US"

        if "cwd" not in kwargs:
            kwargs["cwd"] = "."
        cmd = GcovProgram.__cmd_split + args
        logger.debug(f"Running gcov: '{' '.join(cmd)}' in '{kwargs['cwd']}'")

        return subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            **kwargs,
        )

    def run_with_args(self, args, **kwargs):
        """Run the gcov program

        >>> import platform
        >>> if platform.system() == "Windows":
        ...     print("kill not working on Windows")  # doctest: +SKIP
        ... else:
        ...     GcovProgram("bash").run_with_args(["-c", "exit 1"])
        Traceback (most recent call last):
        ...
        RuntimeError: GCOV returncode was 1.
        >>> if platform.system() == "Windows":
        ...     GcovProgram("bash").run_with_args(["-c", "exit 1"])
        ... else:
        ...     print("kill not working on Windows")  # doctest: +SKIP
        Traceback (most recent call last):
        ...
        RuntimeError: GCOV returncode was 4294967295.
        >>> if platform.system() == "Windows":
        ...     print("kill not working on Windows")  # doctest: +SKIP
        ... else:
        ...     GcovProgram("bash").run_with_args(["-c", "kill $$"])
        Traceback (most recent call last):
        ...
        RuntimeError: GCOV returncode was -15 (exited by signal).
        >>> if platform.system() == "Windows":
        ...     GcovProgram("bash").run_with_args(["-c", "kill $$"])
        ... else:
        ...     print("kill not working on Windows")  # doctest: +SKIP
        Traceback (most recent call last):
        ...
        RuntimeError: GCOV returncode was 15.
        """
        gcov_process = self.__get_gcov_process(args, **kwargs)
        out, err = gcov_process.communicate()
        if gcov_process.returncode < 0:
            raise RuntimeError(
                f"GCOV returncode was {gcov_process.returncode} (exited by signal)."
            )
        elif gcov_process.returncode != 0:
            raise RuntimeError(f"GCOV returncode was {gcov_process.returncode}.")

        return (out, err)


def run_gcov_and_process_files(abs_filename, covdata, options, error, chdir):
    fname = None
    out = None
    err = None
    try:
        gcov_cmd = GcovProgram(options.gcov_cmd)
        gcov_cmd.identify_and_cache_capabilities()

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
            )

            # find the files that gcov created
            active_gcov_files, all_gcov_files = select_gcov_files_from_stdout(
                out,
                gcov_filter=options.gcov_filter,
                gcov_exclude=options.gcov_exclude,
                chdir=chdir,
            )

            if unknown_cla_re.search(err):
                # gcov tossed errors: throw exception
                raise RuntimeError(f"Error in gcov command line: {err}")
            elif source_re.search(err):
                # gcov tossed errors: try the next potential_wd
                error(err)
                done = False
            else:
                # Process *.gcov files
                for fname in active_gcov_files:
                    process_gcov_data(fname, covdata, abs_filename, options)
                done = True

            if options.keep and done:
                basename = os.path.basename(abs_filename)
                for file in active_gcov_files:
                    dir, filename = os.path.split(file)
                    os.replace(file, os.path.join(dir, f"{basename}.{filename}"))

            for filepath in (
                all_gcov_files - active_gcov_files
                if options.keep and done
                else all_gcov_files
            ):
                if os.path.exists(filepath):
                    os.remove(filepath)

    except Exception:
        logger.error(
            f"Trouble processing {abs_filename!r} with working directory {chdir!r}.\n"
            f"Stdout of gcov was >>{out}<< End of stdout\n"
            f"Stderr of gcov was >>{err}<< End of stderr\n"
            f"Current processed gcov file was {fname!r}.\n"
            "Use option --verbose to get extended informations."
        )
        raise

    return done


def select_gcov_files_from_stdout(out, gcov_filter, gcov_exclude, chdir):
    active_files = set([])
    all_files = set([])

    for line in out.splitlines():
        found = output_re.search(line.strip())
        if found is None:
            continue

        fname = found.group(1)
        full = os.path.join(chdir, fname)
        all_files.add(full)

        filtered, excluded = apply_filter_include_exclude(
            fname, gcov_filter, gcov_exclude
        )

        if filtered:
            logger.debug(f"Filtering gcov file {fname}")
            continue

        if excluded:
            logger.debug(f"Excluding gcov file {fname}")
            continue

        active_files.add(full)

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
