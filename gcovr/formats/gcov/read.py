# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.2
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2024 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import gzip
import json
import logging
import os
import re
import shlex
import subprocess  # nosec # Commands are trusted.
from threading import Lock
from typing import Callable, List, Optional, Set, Tuple

from ...options import Options
from ...merging import (
    FUNCTION_MAX_LINE_MERGE_OPTIONS,
    GcovrMergeAssertionError,
    insert_branch_coverage,
    insert_condition_coverage,
    insert_function_coverage,
    insert_line_coverage,
    merge_covdata,
)

from ...utils import (
    search_file,
    commonpath,
    is_fs_case_insensitive,
    fix_case_of_path,
    get_md5_hexdigest,
)
from .workers import Workers, locked_directory
from ...coverage import (
    BranchCoverage,
    ConditionCoverage,
    CovData,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
)
from ...merging import get_merge_mode_from_options, insert_file_coverage
from ...exclusions import apply_all_exclusions
from ...decision_analysis import DecisionParser

from .parser import parse_metadata, parse_coverage


LOGGER = logging.getLogger("gcovr")

output_re = re.compile(r"[Cc]reating [`'](.*)'$")
source_error_re = re.compile(
    r"(?:[Cc](?:annot|ould not) open (?:source|graph) file|: No such file or directory)"
)
output_error_re = re.compile(
    r"(?:[Cc](?:annot|ould not) open output file|Operation not permitted|Permission denied|Read-only file system)"
)
unknown_cla_re = re.compile(r"Unknown command line argument")


def read_report(options: Options) -> CovData:
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
        lambda: {"covdata": dict(), "to_erase": set(), "options": options},
    ) as pool:
        LOGGER.debug(f"Pool started with {pool.size()} threads")
        for file_ in datafiles:
            pool.add(process_file, file_)
        contexts = pool.wait()

    to_erase = set()
    covdata = dict()
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
    search_path: str, exclude_dirs: List[re.Pattern]
) -> List[str]:
    """Find .gcov and .gcov.json.gz files under the given search path."""
    if os.path.isfile(search_path):
        LOGGER.debug(f"Using given file {search_path}")
        gcov_files = [search_path]
    else:
        LOGGER.debug(f"Scanning directory {search_path} for gcov files...")
        gcov_files = list(
            search_file(
                re.compile(r".*\.gcov(?:\.json\.gz)?$").match,
                search_path,
                exclude_dirs=exclude_dirs,
            )
        )
        LOGGER.debug(f"Found {len(gcov_files)} files (and will process all of them)")
    return gcov_files


def find_datafiles(search_path: str, exclude_dirs: List[re.Pattern]) -> List[str]:
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
                re.compile(r".*\.gc(da|no)$").match,
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
def process_gcov_json_data(data_fname: str, covdata: CovData, options) -> None:
    with gzip.open(data_fname, "rt", encoding="UTF-8") as fh_in:
        gcov_json_data = json.loads(fh_in.read())

    for file in gcov_json_data["files"]:
        fname = os.path.normpath(
            os.path.join(gcov_json_data["current_working_directory"], file["file"])
        )
        LOGGER.debug(f"Parsing coverage data for file {fname}")

        # Return if the filename does not match the filter
        # Return if the filename matches the exclude pattern
        filtered, excluded = apply_filter_include_exclude(
            fname, options.filter, options.exclude
        )

        if filtered:
            LOGGER.debug(f"  Filtering coverage data for file {fname}")
            continue

        if excluded:
            LOGGER.debug(f"  Excluding coverage data for file {fname}")
            continue

        if file["file"] == "<stdin>":
            message = f"Got sourcefile {file['file']}, using empty lines."
            LOGGER.info(message)
            source_lines = [b"" for _ in range(file["lines"][-1]["line_number"])]
            source_lines[0] = f"/* {message} */".encode()
        else:
            with open(fname, "rb") as fh_in:
                source_lines = fh_in.read().splitlines()
            lines = len(source_lines)
            max_line_from_cdata = (
                file["lines"][-1]["line_number"] if file["lines"] else 1
            )
            if lines < max_line_from_cdata:
                LOGGER.warning(
                    f"File {fname} has {lines} line(s) but coverage data has {max_line_from_cdata} line(s)."
                )
                # Python ranges are exclusive. We want to iterate over all lines, including
                # that last line. Thus, we have to add a +1 to include that line.
                for _ in range(lines, max_line_from_cdata):
                    source_lines.append(b"/*EOF*/")

        file_cov = FileCoverage(fname)
        for line in file["lines"]:
            line_cov = insert_line_coverage(
                file_cov,
                LineCoverage(
                    line["line_number"],
                    count=line["count"],
                    function_name=line.get("function_name"),
                    block_ids=line["block_ids"],
                    md5=get_md5_hexdigest(source_lines[line["line_number"] - 1]),
                ),
            )
            for index, branch in enumerate(line["branches"]):
                insert_branch_coverage(
                    line_cov,
                    index,
                    BranchCoverage(
                        branch["source_block_id"],
                        branch["count"],
                        fallthrough=branch["fallthrough"],
                        throw=branch["throw"],
                        destination_blockno=branch["destination_block_id"],
                    ),
                )
            for index, condition in enumerate(line.get("conditions", [])):
                insert_condition_coverage(
                    line_cov,
                    index,
                    ConditionCoverage(
                        condition["count"],
                        condition["covered"],
                        condition["not_covered_true"],
                        condition["not_covered_false"],
                    ),
                )
        for function in file["functions"]:
            # Use 100% only if covered == total.
            if function["blocks_executed"] == function["blocks"]:
                blocks = 100.0
            else:
                # There is at least one uncovered item.
                # Round to 1 decimal and clamp to max 99.9%.
                ratio = function["blocks_executed"] / function["blocks"]
                blocks = min(99.9, round(ratio * 100.0, 1))

            insert_function_coverage(
                file_cov,
                FunctionCoverage(
                    function["name"],
                    function["demangled_name"],
                    lineno=function["start_line"],
                    count=function["execution_count"],
                    blocks=blocks,
                    start=(function["start_line"], function["start_column"]),
                    end=(function["end_line"], function["end_column"]),
                ),
                FUNCTION_MAX_LINE_MERGE_OPTIONS,
            )

        encoded_source_lines = [
            line.decode(options.source_encoding, errors="replace")
            for line in source_lines
        ]
        LOGGER.debug(f"Apply exclusions for {fname}")
        apply_all_exclusions(file_cov, lines=encoded_source_lines, options=options)

        if options.show_decision:
            decision_parser = DecisionParser(file_cov, encoded_source_lines)
            decision_parser.parse_all_lines()

        LOGGER.debug(f"Merge coverage data for {fname}")
        insert_file_coverage(covdata, file_cov, get_merge_mode_from_options(options))


#
# Process a single gcov datafile
#
def process_gcov_data(
    data_fname: str,
    gcda_fname: Optional[str],
    covdata: CovData,
    options: Options,
    current_dir: str = None,
) -> None:
    with open(
        data_fname, "r", encoding=options.source_encoding, errors="replace"
    ) as fh_in:
        lines = fh_in.read().splitlines()

    # Find the source file
    # TODO: instead of heuristics, use "working directory" if available
    metadata = parse_metadata(lines)
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

    # Return if the filename does not match the filter
    # Return if the filename matches the exclude pattern
    filtered, excluded = apply_filter_include_exclude(
        fname, options.filter, options.exclude
    )

    if filtered:
        LOGGER.debug(f"  Filtering coverage data for file {fname}")
        return

    if excluded:
        LOGGER.debug(f"  Excluding coverage data for file {fname}")
        return

    LOGGER.debug(f"Parsing coverage data for file {fname}")
    key = os.path.normpath(fname)

    coverage, source_lines = parse_coverage(
        lines,
        filename=key,
        ignore_parse_errors=options.gcov_ignore_parse_errors,
    )

    LOGGER.debug(f"Apply exclusions for {fname}")
    apply_all_exclusions(coverage, lines=source_lines, options=options)

    if options.show_decision:
        decision_parser = DecisionParser(coverage, source_lines)
        decision_parser.parse_all_lines()

    LOGGER.debug(f"Merge coverage data for {fname}")
    insert_file_coverage(covdata, coverage, get_merge_mode_from_options(options))


def guess_source_file_name(
    source_from_gcov: str,
    data_fname: str,
    gcda_fname: str,
    root_dir: str,
    starting_dir: str,
    obj_dir: str,
    current_dir: str = None,
) -> str:
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


def guess_source_file_name_heuristics(
    source_from_gcov: str,
    data_fname: str,
    gcda_fname: str,
    current_dir: str,
    root_dir: str,
    starting_dir: str,
    obj_dir: str,
) -> str:
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
    filename: str, covdata: CovData, options: Options, to_erase: Set[str]
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

    errors = []

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
        errors.append(str(exc).split("\n"))

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
        [v in options.gcov_ignore_errors for v in ["all", "no_working_dir_found"]]
    ):
        raise RuntimeError(errors_output)


def find_potential_working_directories_via_objdir(
    abs_filename: str, objdir: str, error: Callable[[str], None]
) -> List[str]:
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
        "was run using --gcov-object-directory=%s\n" % objdir
    )

    return []


class GcovProgram:
    __lock = Lock()
    __cmd = None
    __cmd_split = None
    __default_options = []
    __exitcode_to_ignore = None
    __use_json_format_if_available = None
    __help_output = None
    __version_output = None

    class LockContext(object):
        def __init__(self, lock: Lock):
            self.lock = lock

        def __enter__(self):
            self.lock.acquire()

        def __exit__(self, *_):
            self.lock.release()

    def __init__(self, cmd: str, options: Options):
        with GcovProgram.LockContext(GcovProgram.__lock):
            GcovProgram.__use_json_format_if_available = options.exclude_calls
            if GcovProgram.__cmd is None:
                GcovProgram.__cmd = cmd
                # If the first element of cmd - the executable name - has embedded spaces
                # (other than within quotes), it probably includes extra arguments.
                GcovProgram.__cmd_split = shlex.split(GcovProgram.__cmd)
            elif GcovProgram.__cmd != cmd:
                raise AssertionError(
                    f"Gcov command must not be changed, expected '{GcovProgram.__cmd}', got '{cmd}'"
                )

    def identify_and_cache_capabilities(self) -> None:
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
                    if self.__check_gcov_version_content("JSON format version: 2"):
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
            if GcovProgram.__exitcode_to_ignore is None:
                GcovProgram.__exitcode_to_ignore = [0]  # SUCCESS
                if not self.__check_gcov_help_content("LLVM"):
                    GcovProgram.__exitcode_to_ignore.append(6)  # WRITE GCOV ERROR

    def __get_help_output(self) -> str:
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

    def __get_version_output(self) -> str:
        if GcovProgram.__version_output is None:
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

    def get_default_options(self) -> List[str]:
        return GcovProgram.__default_options

    def __get_gcov_process(self, args: List[str], **kwargs) -> subprocess.Popen:
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

    def run_with_args(self, args: List[str], **kwargs) -> Tuple[str, str]:
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
        LOGGER.debug(
            f"GCOV return code was {gcov_process.returncode}, stderr was:\n{err}<<"
        )
        if gcov_process.returncode < 0:
            raise RuntimeError(
                f"GCOV returncode was {gcov_process.returncode} (exited by signal).\n"
                f"Stdout of gcov was >>{out}<< End of stdout\n"
                f"Stderr of gcov was >>{err}<< End of stderr"
            )
        elif gcov_process.returncode not in GcovProgram.__exitcode_to_ignore:
            raise RuntimeError(
                f"GCOV returncode was {gcov_process.returncode}.\n"
                f"Stdout of gcov was >>{out}<< End of stdout\n"
                f"Stderr of gcov was >>{err}<< End of stderr"
            )

        return (out, err)


def run_gcov_and_process_files(
    abs_filename: str,
    covdata: CovData,
    options: Options,
    error: Callable[[str], None],
    chdir: str,
) -> bool:
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
            except Exception:  # pragma: no cover # nosec
                pass
            object_directory = os.path.dirname(abs_filename)
            try:
                object_directory = os.path.relpath(object_directory, chdir)
            except Exception:  # pragma: no cover # nosec
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
            else:
                ignore_source_errors = options.gcov_ignore_errors is not None and any(
                    [
                        v in options.gcov_ignore_errors
                        for v in ["all", "source_not_found"]
                    ]
                )
                ignore_output_errors = options.gcov_ignore_errors is not None and any(
                    [v in options.gcov_ignore_errors for v in ["all", "output_error"]]
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
                        active_gcov_files = [
                            f for f in active_gcov_files if os.path.exists(f)
                        ]

                    # Process *.gcov files
                    for gcov_filename in active_gcov_files:
                        if not os.path.exists(gcov_filename):  # pragma: no cover
                            raise RuntimeError(
                                f"Sanity check failed, output file {gcov_filename} doesn't exist but no error from GCOV detected."
                            )

                        if gcov_filename.endswith(".gcov"):
                            process_gcov_data(
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
                    dir, filename = os.path.split(file)
                    os.replace(file, os.path.join(dir, f"{basename}.{filename}"))

            for filepath in (
                all_gcov_files - active_gcov_files
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
    out: str, gcov_filter: List[re.Pattern], gcov_exclude: List[re.Pattern], chdir: str
) -> Tuple[List[str], List[str]]:
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
            LOGGER.debug(f"Filtering gcov file {fname}")
            continue

        if excluded:
            LOGGER.debug(f"Excluding gcov file {fname}")
            continue

        active_files.add(full)

    return active_files, all_files


#
#  Process Already existing gcov files
#
def process_existing_gcov_file(
    filename: str, covdata: CovData, options: Options, to_erase: List[str]
) -> None:
    filtered, excluded = apply_filter_include_exclude(
        filename, options.gcov_filter, options.gcov_exclude
    )

    if filtered:
        LOGGER.debug(f"This gcov file does not match the filter: {filename}")
        return

    if excluded:
        LOGGER.debug(f"Excluding gcov file: {filename}")
        return

    if filename.endswith(".gcov"):
        process_gcov_data(filename, None, covdata, options)
    elif filename.endswith(".gcov.json.gz"):
        process_gcov_json_data(filename, covdata, options)
    else:  # pragma: no cover
        raise RuntimeError(f"Unknown gcov output format {filename}.")

    if not options.gcov_keep:
        to_erase.add(filename)


def apply_filter_include_exclude(
    filename: str, include_filters: List[re.Pattern], exclude_filters: List[re.Pattern]
) -> Tuple[bool, bool]:
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
