# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.3
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import gzip
from json import loads as json_loads
import logging
import os
import re
import shlex
import subprocess  # nosec # Commands are trusted.
from threading import Lock
from typing import Any, Callable, Optional

from ...coverage import CoverageContainer
from ...decision_analysis import DecisionParser
from ...exclusions import (
    apply_all_exclusions,
    get_exclusion_options_from_options,
)
from ...filter import Filter, is_file_excluded
from ...merging import (
    GcovrMergeAssertionError,
    get_merge_mode_from_options,
    insert_file_coverage,
    merge_covdata,
)
from ...options import Options
from ...utils import (
    commonpath,
    fix_case_of_path,
    is_fs_case_insensitive,
    search_file,
)
from .parser import (
    json,
    text,
)
from .workers import Workers, locked_directory

LOGGER = logging.getLogger("gcovr")

output_re = re.compile(r"[Cc]reating [`'](.*)'$")
source_error_re = re.compile(
    r"(?:[Cc](?:annot|ould not) open (?:source|graph) file|: No such file or directory)"
)
output_error_re = re.compile(
    r"(?:[Cc](?:annot|ould not) open output file|Operation not permitted|Permission denied|Read-only file system)"
)
unknown_cla_re = re.compile(r"Unknown command line argument")


def read_report(options: Options) -> CoverageContainer:
    """Read data from GCOV output."""
    datafiles = set()

    find_files = find_datafiles
    process_file = process_datafile
    if options.gcov_files:
        find_files = find_existing_gcov_files
        process_file = process_existing_gcov_file

    # Get data files
    if not options.search_paths:
        options.search_paths = [options.root]

        if options.gcov_objdir is not None:
            options.search_paths.append(options.gcov_objdir)

    for search_path in options.search_paths:
        datafiles.update(find_files(search_path, options.gcov_exclude_dirs))

    # Get coverage data
    with Workers(
        options.gcov_parallel,
        lambda: {"covdata": CoverageContainer(), "to_erase": set(), "options": options},
    ) as pool:
        LOGGER.debug(f"Pool started with {pool.size()} threads")
        for file_ in sorted(datafiles):
            pool.add(process_file, file_)
        contexts = pool.wait()

    to_erase = set()
    covdata = CoverageContainer()
    for context in contexts:
        covdata = merge_covdata(
            covdata, context["covdata"], get_merge_mode_from_options(options)
        )
        to_erase.update(context["to_erase"])

    for filepath in to_erase:
        if os.path.exists(filepath):
            os.remove(filepath)

    return covdata


def find_existing_gcov_files(
    search_path: str, exclude_dirs: list[re.Pattern[str]]
) -> list[str]:
    """Find .gcov and .gcov.json.gz files under the given search path."""
    if os.path.isfile(search_path):
        LOGGER.debug(f"Using given file {search_path}")
        gcov_files = [search_path]
    else:
        LOGGER.debug(f"Scanning directory {search_path} for gcov files...")
        gcov_files = list(
            search_file(
                lambda fname: re.compile(r".*\.gcov(?:\.json\.gz)?$").match(fname)
                is not None,
                search_path,
                exclude_dirs=exclude_dirs,
            )
        )
        LOGGER.debug(f"Found {len(gcov_files)} files (and will process all of them)")
    return gcov_files


def find_datafiles(search_path: str, exclude_dirs: list[re.Pattern[str]]) -> list[str]:
    """Find .gcda and .gcno files under the given search path.

    The .gcno files will *only* produce uncovered results.
    However, that is useful information when a compilation unit
    is never actually exercised by the test code.
    So we ONLY return them if there's no corresponding .gcda file.
    """
    if os.path.isfile(search_path):
        LOGGER.debug(f"Using given file {search_path}")
        files = [search_path]
    else:
        LOGGER.debug(f"Scanning directory {search_path} for gcda/gcno files...")
        files = list(
            search_file(
                lambda fname: re.compile(r".*\.gc(da|no)$").match(fname) is not None,
                search_path,
                exclude_dirs=exclude_dirs,
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
    LOGGER.debug(
        f"Found {len(files)} files (and will process {len(gcda_files) + len(gcno_files)})"
    )
    return gcda_files + gcno_files


#
# Process a single gcov datafile
#
def process_gcov_json_data(
    data_fname: str, covdata: CoverageContainer, options: Options
) -> None:
    """Process a GCOV JSON output."""

    with gzip.open(data_fname, "rt", encoding="UTF-8") as fh_in:
        gcov_json_data = json_loads(fh_in.read())

    coverage = json.parse_coverage(
        gcov_json_data=gcov_json_data,
        include_filters=options.filter,
        exclude_filters=options.exclude,
        ignore_parse_errors=options.gcov_ignore_parse_errors,
        suspicious_hits_threshold=options.gcov_suspicious_hits_threshold,
        source_encoding=options.source_encoding,
        data_fname=data_fname,
    )

    for file_cov, source_lines in coverage:
        LOGGER.debug(f"Apply exclusions for {file_cov.filename}")
        apply_all_exclusions(
            file_cov,
            lines=source_lines,
            options=get_exclusion_options_from_options(options),
        )

        if options.show_decision:
            decision_parser = DecisionParser(file_cov, source_lines)
            decision_parser.parse_all_lines()

        LOGGER.debug(f"Merge coverage data for {file_cov.filename}")
        insert_file_coverage(covdata, file_cov, get_merge_mode_from_options(options))


#
# Process a single gcov datafile
#
def process_gcov_text_data(
    data_fname: str,
    gcda_fname: Optional[str],
    covdata: CoverageContainer,
    options: Options,
    current_dir: Optional[str] = None,
) -> None:
    """Process a GCOV text output."""
    with open(
        data_fname, "r", encoding=options.source_encoding, errors="replace"
    ) as fh_in:
        lines = fh_in.read().splitlines()

    # Find the source file
    metadata = text.parse_metadata(
        lines, suspicious_hits_threshold=options.gcov_suspicious_hits_threshold
    )
    source = metadata.get("Source")
    if source is None:
        raise RuntimeError("Unexpected value 'None' for metadata 'Source'.")
    # gcov writes filenames with '/' path separators even if the OS
    # separator is different, so we replace it with the correct separator
    source = source.replace("/", os.sep)

    fname = guess_source_file_name(
        source,
        data_fname,
        gcda_fname,
        root_dir=options.root_dir,
        starting_dir=options.starting_dir,
        obj_dir=(
            None
            if options.gcov_objdir is None
            else os.path.abspath(options.gcov_objdir)
        ),
        current_dir=current_dir,
    )

    if is_file_excluded(fname, options.filter, options.exclude):
        return

    LOGGER.debug(f"Parsing coverage data for file {fname}")
    key = os.path.normpath(fname)

    coverage, source_lines = text.parse_coverage(
        lines,
        filename=key,
        data_filename=gcda_fname or data_fname,
        ignore_parse_errors=options.gcov_ignore_parse_errors,
        suspicious_hits_threshold=options.gcov_suspicious_hits_threshold,
    )

    LOGGER.debug(f"Apply exclusions for {fname}")
    apply_all_exclusions(coverage, lines=source_lines, options=options)  # type: ignore [arg-type]

    if options.show_decision:
        decision_parser = DecisionParser(coverage, source_lines)
        decision_parser.parse_all_lines()

    LOGGER.debug(f"Merge coverage data for {fname}")
    insert_file_coverage(covdata, coverage, get_merge_mode_from_options(options))


def guess_source_file_name(
    source_from_gcov: str,
    data_fname: str,
    gcda_fname: Optional[str],
    root_dir: str,
    starting_dir: str,
    obj_dir: Optional[str],
    current_dir: Optional[str] = None,
) -> str:
    """Guess the full source filename."""
    if current_dir is None:
        current_dir = os.getcwd()
    if os.path.isabs(source_from_gcov):
        fname = source_from_gcov
    elif gcda_fname is None:
        fname = guess_source_file_name_via_aliases(
            source_from_gcov, data_fname, current_dir
        )
    else:
        fname = guess_source_file_name_heuristics(
            source_from_gcov,
            data_fname,
            gcda_fname,
            current_dir,
            root_dir,
            starting_dir,
            obj_dir,
        )

    if is_fs_case_insensitive():
        fname = fix_case_of_path(fname)

    LOGGER.debug(
        f"Finding source file corresponding to a gcov data file\n"
        f"  gcov_fname   {data_fname}\n"
        f"  current_dir  {current_dir}\n"
        f"  root         {root_dir}\n"
        f"  starting_dir {starting_dir}\n"
        f"  obj_dir      {obj_dir}\n"
        f"  gcda_fname   {gcda_fname}\n"
        f"  --> fname    {fname}"
    )

    return fname


def guess_source_file_name_via_aliases(
    source_from_gcov: str,
    data_fname: str,
    current_dir: str,
) -> str:
    """Guess the full source filename with path by an alias."""
    common_dir = commonpath([data_fname, current_dir])
    fname = os.path.abspath(os.path.join(common_dir, source_from_gcov))
    if os.path.exists(fname):
        return fname

    initial_fname = fname

    data_fname_dir = os.path.dirname(data_fname)
    fname = os.path.abspath(os.path.join(data_fname_dir, source_from_gcov))
    if os.path.exists(fname):
        return fname

    # @latk-2018: The original code is *very* insistent
    # on returning the initial guess. Why?
    return initial_fname


def guess_source_file_name_heuristics(  # pylint: disable=too-many-return-statements
    source_from_gcov: str,
    data_fname: str,
    gcda_fname: str,
    current_dir: str,
    root_dir: str,
    starting_dir: str,
    obj_dir: Optional[str],
) -> str:
    """Guess the full source filename with path by a heuristic."""
    # 0. Try using the path to the gcov file
    fname = os.path.join(os.path.dirname(data_fname), source_from_gcov)
    if os.path.exists(fname):
        return fname

    LOGGER.debug("Fallback to heuristic of gcovr 5.1")

    # 1. Try using the current working directory as the source directory
    fname = os.path.join(current_dir, source_from_gcov)
    if os.path.exists(fname):
        return fname

    # 2. Try using the path to common prefix with the root_dir as the source directory
    fname = os.path.join(root_dir, source_from_gcov)
    if os.path.exists(fname):
        return fname

    # 3. Try using the starting directory as the source directory
    fname = os.path.join(starting_dir, source_from_gcov)
    if os.path.exists(fname):
        return fname

    # 4. Try using relative path from object dir
    if obj_dir is not None:
        fname = os.path.normpath(os.path.join(obj_dir, source_from_gcov))
        if os.path.exists(fname):
            return fname

    # Get path of gcda file
    gcda_fname_dir = os.path.dirname(gcda_fname)

    # 5. Try using the path to the gcda as the source directory
    fname = os.path.join(gcda_fname_dir, source_from_gcov)
    if os.path.exists(fname):
        return os.path.normpath(fname)

    # 6. Try using the path to the gcda file as the source directory, removing the path part from the gcov file
    fname = os.path.join(gcda_fname_dir, os.path.basename(source_from_gcov))
    return fname


def process_datafile(
    filename: str, covdata: CoverageContainer, options: Options, to_erase: set[str]
) -> None:
    r"""Run gcovr in a suitable directory to collect coverage from gcda files.

    Params:
        filename (path): the path to a gcda or gcno file
        covdata (dict, mutable): the global covdata dictionary
        options (object): the configuration options namespace
        to_erase (set, mutable): files that should be deleted later

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

    Ideally, the build process only runs gcc from *one* directory
    and the user can provide this directory as the ``--gcov-object-directory``.
    If it exists, we try that path as a work dir,
    If the path is relative, it is resolved relative to the gcovr cwd and the
    object file location.

    We next try the ``--root`` directory.
    TODO: should probably also be the gcovr start directory.

    If none of those work, we assume that
    the object files are in a subdirectory of the gcc working directory,
    i.e. we can walk the directory tree upwards.

    All of this works fine unless gcc was invoked like ``gcc -o ../path``,
    i.e. the object files are in a sibling directory.
    TODO: So far there is no good way to address this case.
    """
    LOGGER.debug(f"Processing file: {filename}")

    abs_filename = os.path.abspath(filename).replace(
        os.path.sep, "/"
    )  # gcov requires posix style path

    errors = list[str]()

    potential_wd = []

    if options.gcov_objdir:
        potential_wd = find_potential_working_directories_via_objdir(
            abs_filename, options.gcov_objdir, error=errors.append
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

    try:
        for wd in potential_wd:
            done = run_gcov_and_process_files(
                abs_filename,
                covdata,
                options=options,
                error=errors.append,
                chdir=wd,
            )

            if options.gcov_delete:
                if not abs_filename.endswith("gcno"):
                    to_erase.add(abs_filename)

            if done:
                return
    # This exception fails fast
    except GcovrMergeAssertionError as exc:
        errors += str(exc).split("\n")

    errors_output = "\n\t".join(errors)
    errors_output = (
        f"GCOV produced the following errors processing {filename}:\n"
        f"\t{errors_output}\n"
        "\t(gcovr could not infer a working directory that resolved it.)\n"
        "To ignore this error use option --gcov-ignore-errors=no_working_dir_found."
    )
    LOGGER.error(errors_output)

    # Check if error shall be ignored
    if options.gcov_ignore_errors is None or not any(
        v in options.gcov_ignore_errors for v in ["all", "no_working_dir_found"]
    ):
        raise RuntimeError(errors_output)


def find_potential_working_directories_via_objdir(
    abs_filename: str, objdir: str, error: Callable[[str], None]
) -> list[str]:
    """Find the potential working directories."""
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
        f"was run using --gcov-object-directory={objdir}\n"
    )

    return []


class GcovProgram:
    """Class to execute GCOV command with a set of auto-detected options"""

    __lock = Lock()
    __cmd: str = ""
    __cmd_split = list[str]()
    __default_options = list[str]()
    __exitcode_to_ignore = list[int]([0])
    __use_json_format_if_available: bool = True
    __help_output: str = ""
    __version_output: str = ""

    class LockContext:
        """Context handler for locking a section in multithreaded executions."""

        def __init__(self, lock: Lock) -> None:
            self.lock = lock

        def __enter__(self) -> None:
            self.lock.acquire()

        def __exit__(self, *_: Any) -> None:
            self.lock.release()

    def __init__(self, cmd: str, options: Options) -> None:
        with GcovProgram.LockContext(GcovProgram.__lock):
            GcovProgram.__use_json_format_if_available = options.exclude_calls
            if not GcovProgram.__cmd:
                GcovProgram.__cmd = cmd
                # If the first element of cmd - the executable name - has embedded spaces
                # (other than within quotes), it probably includes extra arguments.
                GcovProgram.__cmd_split = shlex.split(GcovProgram.__cmd)
            elif GcovProgram.__cmd != cmd:
                raise AssertionError(
                    f"Gcov command must not be changed, expected '{GcovProgram.__cmd}', got '{cmd}'"
                )

    def identify_and_cache_capabilities(self) -> None:
        """Check the capabilities of GCOVR once."""
        with GcovProgram.LockContext(GcovProgram.__lock):
            if not GcovProgram.__default_options:
                GcovProgram.__default_options = [
                    "--branch-counts",
                    "--branch-probabilities",
                    "--all-blocks",
                ]

                if (
                    GcovProgram.__use_json_format_if_available
                    and self.__check_gcov_help_content("--json-format")
                ):
                    if self.__check_gcov_version_content(
                        f"JSON format version: {json.GCOV_JSON_VERSION}"
                    ):
                        LOGGER.debug("GCOV capabilities: JSON format available.")
                        GcovProgram.__default_options.append("--json-format")
                        if self.__check_gcov_help_content("--condition"):
                            LOGGER.debug(
                                "GCOV capabilities: Condition coverage available."
                            )
                            GcovProgram.__default_options.append("--condition")
                    else:
                        LOGGER.debug(
                            "GCOV capabilities: Unsupported JSON format detected."
                        )

                if self.__check_gcov_help_content("--demangled-names"):
                    LOGGER.debug("GCOV capabilities: Demangled names available.")
                    GcovProgram.__default_options.append("--demangled-names")

                if self.__check_gcov_help_content("--hash-filenames"):
                    LOGGER.debug("GCOV capabilities: Hashing of filenames available.")
                    GcovProgram.__default_options.append("--hash-filenames")
                elif self.__check_gcov_help_content("--preserve-paths"):
                    LOGGER.debug("GCOV capabilities: Preserve of paths available.")
                    GcovProgram.__default_options.append("--preserve-paths")
                else:
                    LOGGER.warning(
                        "Options '--hash-filenames' and '--preserve-paths' are not "
                        f"supported by '{GcovProgram.__cmd}'. Source files with "
                        "identical file names may result in incorrect coverage."
                    )

                if not self.__check_gcov_help_content("LLVM"):
                    GcovProgram.__exitcode_to_ignore.append(6)  # WRITE GCOV ERROR

    def __get_help_output(self) -> str:
        if not GcovProgram.__help_output:
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
            if not GcovProgram.__help_output:
                # gcov tossed errors: throw exception
                raise RuntimeError("Error in gcov command line, couldn't get help.")

        return GcovProgram.__help_output

    def __get_version_output(self) -> str:
        if not GcovProgram.__version_output:
            gcov_process = self.__get_gcov_process(
                ["--version"],
                universal_newlines=True,
            )
            out, _ = gcov_process.communicate(timeout=30)

            if gcov_process.returncode:  # pragma: no cover
                # gcov tossed errors: throw exception
                raise RuntimeError(
                    "Error in gcov command line, couldn't get version information."
                )
            # gcov execution was successful, help argument is not supported.
            GcovProgram.__version_output = out

        return GcovProgram.__version_output

    def __check_gcov_help_content(self, option: str) -> bool:
        if option in self.__get_help_output():
            return True

        return False

    def __check_gcov_version_content(self, option: str) -> bool:
        if option in self.__get_version_output():
            return True

        return False

    def get_default_options(self) -> list[str]:
        """Get the default options for GCOV."""
        return GcovProgram.__default_options

    def __get_gcov_process(
        self, args: list[str], **kwargs: Any
    ) -> "subprocess.Popen[str]":
        # NB: Currently, we will only parse English output
        env = kwargs.pop("env") if "env" in kwargs else dict(os.environ)
        env["LC_ALL"] = "C"
        env["LANGUAGE"] = "en_US"

        if "cwd" not in kwargs:
            kwargs["cwd"] = "."
        cmd = GcovProgram.__cmd_split + args
        LOGGER.debug(f"Running gcov: '{' '.join(cmd)}' in '{kwargs['cwd']}'")

        return subprocess.Popen(  # nosec # We know that we execute gcov tool
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            **kwargs,
        )

    def run_with_args(self, args: list[str], **kwargs: Any) -> tuple[str, str]:
        """Run the gcov program.

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
        LOGGER.debug(
            f"GCOV return code was {gcov_process.returncode}, stderr was:\n{err}<<"
        )
        if gcov_process.returncode < 0:
            raise RuntimeError(
                f"GCOV returncode was {gcov_process.returncode} (exited by signal).\n"
                f"Stdout of gcov was >>{out}<< End of stdout\n"
                f"Stderr of gcov was >>{err}<< End of stderr"
            )

        if gcov_process.returncode not in GcovProgram.__exitcode_to_ignore:
            raise RuntimeError(
                f"GCOV returncode was {gcov_process.returncode}.\n"
                f"Stdout of gcov was >>{out}<< End of stdout\n"
                f"Stderr of gcov was >>{err}<< End of stderr"
            )

        return (out, err)


def run_gcov_and_process_files(
    abs_filename: str,
    covdata: CoverageContainer,
    options: Options,
    error: Callable[[str], None],
    chdir: str,
) -> bool:
    """Run GCOV tool and process the output files."""
    filename = None
    out = None
    err = None
    try:
        gcov_cmd = GcovProgram(options.gcov_cmd, options)
        gcov_cmd.identify_and_cache_capabilities()

        # ATTENTION:
        # This lock is essential for parallel processing because without
        # this there can be name collisions for the generated output files.
        with locked_directory(chdir):
            filename = abs_filename
            # Use try catch because the relpath can fail on Windows for different drives.
            # Do not know how to force this exception therefore ignore coverage.
            try:
                filename = os.path.relpath(filename, chdir)
            except OSError:  # pragma: no cover # nosec
                pass
            object_directory = os.path.dirname(abs_filename)
            try:
                object_directory = os.path.relpath(object_directory, chdir)
            except OSError:  # pragma: no cover # nosec
                pass
            out, err = gcov_cmd.run_with_args(
                [
                    abs_filename,
                    *gcov_cmd.get_default_options(),
                    "--object-directory",
                    object_directory,
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

            ignore_source_errors = options.gcov_ignore_errors is not None and any(
                v in options.gcov_ignore_errors for v in ["all", "source_not_found"]
            )
            ignore_output_errors = options.gcov_ignore_errors is not None and any(
                v in options.gcov_ignore_errors for v in ["all", "output_error"]
            )
            if (
                # GCOV did not find source file and error shall not be ignored
                (source_error_re.search(err) and not ignore_source_errors)
                # GCOV can not write output file and error shall not be ignored
                or (output_error_re.search(err) and not ignore_output_errors)
            ):
                # gcov tossed errors: try the next potential_wd
                error(f"In directory {chdir}:\n{err}")
                done = False
            else:
                if ignore_output_errors:
                    active_gcov_files = set(
                        f for f in active_gcov_files if os.path.exists(f)
                    )

                # Process *.gcov files
                for gcov_filename in active_gcov_files:
                    if not os.path.exists(gcov_filename):  # pragma: no cover
                        raise AssertionError(
                            f"Sanity check failed, output file {gcov_filename} doesn't exist but no error from GCOV detected."
                        )

                    if gcov_filename.endswith(".gcov"):
                        process_gcov_text_data(
                            gcov_filename, filename, covdata, options, chdir
                        )
                    elif gcov_filename.endswith(".gcov.json.gz"):
                        process_gcov_json_data(gcov_filename, covdata, options)
                    else:  # pragma: no cover
                        raise RuntimeError(
                            f"Unknown gcov output format {gcov_filename}."
                        )
                done = True

            if options.gcov_keep and done:
                basename = os.path.basename(abs_filename)
                for file in active_gcov_files:
                    directory, filename = os.path.split(file)
                    os.replace(file, os.path.join(directory, f"{basename}.{filename}"))

            for filepath in (
                list(all_gcov_files - active_gcov_files)
                if options.gcov_keep and done
                else all_gcov_files
            ):
                if os.path.exists(filepath):
                    os.remove(filepath)

    except RuntimeError as exc:
        # If we got an merge assertion error we must end the processing
        done = False
        error(
            f"Trouble processing {abs_filename!r} with working directory {chdir!r}.\n"
            f"Stdout of gcov was >>{out}<< End of stdout\n"
            f"Stderr of gcov was >>{err}<< End of stderr\n"
            f"Exception was >>{str(exc)}<< End of stderr\n"
            f"Current processed gcov file was {filename!r}.\n"
            "Use option --verbose to get extended information."
        )

    return done


def select_gcov_files_from_stdout(
    out: str,
    gcov_filter: list[Filter],
    gcov_exclude: list[Filter],
    chdir: str,
) -> tuple[set[str], set[str]]:
    """Parse the output to get the list of files to use and all files (unfiltered)."""
    active_files = set()
    all_files = set()

    for line in out.splitlines():
        found = output_re.search(line.strip())
        if found is None:
            continue

        fname = found.group(1)
        full = os.path.join(chdir, fname)
        all_files.add(full)

        if is_file_excluded(fname, gcov_filter, gcov_exclude):
            continue

        active_files.add(full)

    return active_files, all_files


#
#  Process Already existing gcov files
#
def process_existing_gcov_file(
    filename: str, covdata: CoverageContainer, options: Options, to_erase: set[str]
) -> None:
    """Process an existing GCOV filename."""
    if is_file_excluded(filename, options.gcov_filter, options.gcov_exclude):
        LOGGER.debug(f"Excluding gcov file: {filename}")

    if filename.endswith(".gcov"):
        process_gcov_text_data(filename, None, covdata, options)
    elif filename.endswith(".gcov.json.gz"):
        process_gcov_json_data(filename, covdata, options)
    else:  # pragma: no cover
        raise RuntimeError(f"Unknown gcov output format {filename}.")

    if not options.gcov_keep:
        to_erase.add(filename)
