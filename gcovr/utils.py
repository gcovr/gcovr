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

from __future__ import annotations
from argparse import ArgumentTypeError
from typing import Type
import logging
import os
import re
import sys
from contextlib import contextmanager

logger = logging.getLogger("gcovr")


class LoopChecker(object):
    def __init__(self):
        self._seen = set()

    def already_visited(self, path):
        st = os.stat(path)
        key = (st.st_dev, st.st_ino)
        if key in self._seen:
            return True

        self._seen.add(key)
        return False


if (sys.platform == "win32") and (sys.version_info < (3, 8)):
    # Only used for old python versions. Function can be treated as stable.
    from nt import _getfinalpathname

    DOS_DEVICE_PATH_PREFIX = "\\\\?\\"
    DOS_DEVICE_PATH_PREFIX_UNC = DOS_DEVICE_PATH_PREFIX + "UNC\\"

    def realpath(path):
        path = os.path.realpath(path)
        # If file exist try to resolve the symbolic links
        if os.path.exists(path):
            has_prefix = path.startswith(DOS_DEVICE_PATH_PREFIX)
            path = _getfinalpathname(path)
            if not has_prefix and path.startswith(DOS_DEVICE_PATH_PREFIX):
                if path.startswith(DOS_DEVICE_PATH_PREFIX_UNC):
                    path = path[len(DOS_DEVICE_PATH_PREFIX_UNC) :]
                else:
                    path = path[len(DOS_DEVICE_PATH_PREFIX) :]
        return path

else:
    realpath = os.path.realpath


def get_os_independent_path(path):
    return path.replace(os.path.sep, "/")


def search_file(predicate, path, exclude_dirs):
    """
    Given a search path, recursively descend to find files that satisfy a
    predicate.
    """
    if path is None or path == ".":
        path = os.getcwd()
    elif not os.path.exists(path):
        raise IOError("Unknown directory '" + path + "'")

    loop_checker = LoopChecker()
    for root, dirs, files in os.walk(os.path.abspath(path), followlinks=True):
        # Check if we've already visited 'root' through the magic of symlinks
        if loop_checker.already_visited(root):
            dirs[:] = []
            continue

        dirs[:] = [
            d
            for d in dirs
            if not any(exc.match(os.path.join(root, d)) for exc in exclude_dirs)
        ]
        root = os.path.abspath(root)

        for name in files:
            if predicate(name):
                yield os.path.abspath(os.path.join(root, name))


def commonpath(files):
    r"""Find the common prefix of all files.

    This differs from the standard library os.path.commonpath():
     - We first normalize all paths to a realpath.
     - We return a path with a trailing path separator.

    No common path exists under the following circumstances:
     - on Windows when the paths have different drives.
       E.g.: commonpath([r'C:\foo', r'D:\foo']) == ''
     - when the `files` are empty.

    Arguments:
        files (list): the input paths, may be relative or absolute.

    Returns: str
        The common prefix directory as a relative path.
        Always ends with a path separator.
        Returns the empty string if no common path exists.
    """
    if not files:
        return ""

    if len(files) == 1:
        prefix_path = os.path.dirname(realpath(files[0]))
    else:
        split_paths = [realpath(path).split(os.path.sep) for path in files]
        # We only have to compare the lexicographically minimum and maximum
        # paths to find the common prefix of all, e.g.:
        #   /a/b/c/d  <- min
        #   /a/b/d
        #   /a/c/a    <- max
        #
        # compare:
        # https://github.com/python/cpython/blob/3.6/Lib/posixpath.py#L487
        min_path = min(split_paths)
        max_path = max(split_paths)
        common = min_path  # assume that min_path is a prefix of max_path
        for i in range(min(len(min_path), len(max_path))):
            if min_path[i] != max_path[i]:
                common = min_path[:i]  # disproven, slice for actual prefix
                break
        prefix_path = os.path.sep.join(common)

    # make the path relative and add a trailing slash
    if prefix_path:
        prefix_path = os.path.join(os.path.relpath(prefix_path), "")
    return prefix_path


#
# Get global statistics
#
def get_global_stats(covdata):
    lines_total = 0
    lines_covered = 0
    functions_total = 0
    functions_covered = 0
    branches_total = 0
    branches_covered = 0

    keys = list(covdata.keys())

    for key in keys:
        (total, covered, _) = covdata[key].line_coverage()
        lines_total += total
        lines_covered += covered

        (total, covered, _) = covdata[key].function_coverage()
        functions_total += total
        functions_covered += covered

        (total, covered, _) = covdata[key].branch_coverage()
        branches_total += total
        branches_covered += covered

    percent = calculate_coverage(lines_covered, lines_total)
    percent_functions = calculate_coverage(functions_covered, functions_total)
    percent_branches = calculate_coverage(branches_covered, branches_total)

    return (
        lines_total,
        lines_covered,
        percent,
        functions_total,
        functions_covered,
        percent_functions,
        branches_total,
        branches_covered,
        percent_branches,
    )


def summarize_file_coverage(coverage, root_filter):
    filename = presentable_filename(coverage.filename, root_filter=root_filter)

    branch_total, branch_covered, branch_percent = coverage.branch_coverage()
    line_total, line_covered, line_percent = coverage.line_coverage()
    function_total, function_covered, function_percent = coverage.function_coverage()
    return (
        filename,
        line_total,
        line_covered,
        line_percent,
        branch_total,
        branch_covered,
        branch_percent,
        function_total,
        function_covered,
        function_percent,
    )


def calculate_coverage(covered, total, nan_value=0.0):
    coverage = nan_value
    if total != 0:
        coverage = round(100.0 * covered / total, 1)
        # If we get 100.0% and not all branches are covered use 99.9%
        if (coverage == 100.0) and (covered != total):
            coverage = 99.9

    return coverage


class FilterOption:
    NonEmpty: Type[NonEmptyFilterOption]

    def __init__(self, regex, path_context=None):
        self.regex = regex
        self.path_context = os.getcwd() if path_context is None else path_context

    def build_filter(self):
        # Try to detect unintended backslashes and warn.
        # Later, the regex engine may or may not raise a syntax error.
        # An unintended backslash is a literal backslash r"\\",
        # or a regex escape that doesn't exist.
        (suggestion, bs_count) = re.subn(
            r"\\\\|\\(?=[^\WabfnrtuUvx0-9AbBdDsSwWZ])", "/", self.regex
        )
        if bs_count:
            logger.warning("filters must use forward slashes as path separators")
            logger.warning(f"your filter : {self.regex}")
            logger.warning(f"did you mean: {suggestion}")

        isabs = self.regex.startswith("/")
        if not isabs and (sys.platform == "win32"):
            # Starts with a drive letter
            isabs = re.match(r"^[A-Za-z]:/", self.regex)

        if isabs:
            return AbsoluteFilter(self.regex)
        else:
            return RelativeFilter(self.path_context, self.regex)


class NonEmptyFilterOption(FilterOption):
    def __init__(self, regex, path_context=None):
        if not regex:
            raise ArgumentTypeError("filter cannot be empty")
        super(NonEmptyFilterOption, self).__init__(regex, path_context)


FilterOption.NonEmpty = NonEmptyFilterOption


class Filter(object):
    def __init__(self, pattern):
        cwd = os.getcwd()
        # Guessing if file system is case insensitive.
        # The working directory is not the root and accessible in upper and lower case.
        is_fs_case_insensitive = (
            (cwd != os.path.sep)
            and os.path.exists(cwd.upper())
            and os.path.exists(cwd.lower())
        )
        flags = re.IGNORECASE if is_fs_case_insensitive else 0
        self.pattern = re.compile(pattern, flags)

    def match(self, path):
        os_independent_path = get_os_independent_path(path)
        return self.pattern.match(os_independent_path)

    def __str__(self):
        return "{name}({pattern})".format(
            name=type(self).__name__, pattern=self.pattern.pattern
        )


class AbsoluteFilter(Filter):
    def match(self, path):
        path = realpath(path)
        return super(AbsoluteFilter, self).match(path)


class RelativeFilter(Filter):
    def __init__(self, root, pattern):
        super(RelativeFilter, self).__init__(pattern)
        self.root = realpath(root)

    def match(self, path):
        path = realpath(path)

        # On Windows, a relative path can never cross drive boundaries.
        # If so, the relative filter cannot match.
        if sys.platform == "win32":
            path_drive, _ = os.path.splitdrive(path)
            root_drive, _ = os.path.splitdrive(self.root)
            if path_drive != root_drive:
                return None

        relpath = os.path.relpath(path, self.root)
        return super(RelativeFilter, self).match(relpath)

    def __str__(self):
        return "RelativeFilter({} root={})".format(self.pattern.pattern, self.root)


class AlwaysMatchFilter(Filter):
    def __init__(self):
        super(AlwaysMatchFilter, self).__init__("")

    def match(self, path):
        return True


class DirectoryPrefixFilter(Filter):
    def __init__(self, directory):
        path = realpath(directory)
        os_independent_path = get_os_independent_path(path)
        pattern = re.escape(f"{os_independent_path}/")
        super(DirectoryPrefixFilter, self).__init__(pattern)

    def match(self, path):
        realpath = os.path.normpath(path)
        return super(DirectoryPrefixFilter, self).match(realpath)


def configure_logging() -> None:
    logging.basicConfig(
        format="(%(levelname)s) %(message)s",
        stream=sys.stderr,
        level=logging.INFO,
    )

    def exception_hook(exc_type, exc_value, exc_traceback) -> None:
        logging.exception(
            "Uncaught EXCEPTION", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = exception_hook


def sort_coverage(
    covdata, show_branch, by_num_uncovered=False, by_percent_uncovered=False
):
    """Sort a coverage dict.

    covdata (dict): the coverage dictionary
    show_branch (bool): select branch coverage (True) or line coverage (False)
    by_num_uncovered, by_percent_uncovered (bool):
        select the sort mode. By default, sort alphabetically.

    returns: the sorted keys
    """

    def num_uncovered_key(key):
        cov = covdata[key]
        (total, covered, _) = (
            cov.branch_coverage() if show_branch else cov.line_coverage()
        )
        uncovered = total - covered
        return uncovered

    def percent_uncovered_key(key):
        cov = covdata[key]
        (total, covered, _) = (
            cov.branch_coverage() if show_branch else cov.line_coverage()
        )
        if covered:
            return -1.0 * covered / total
        elif total:
            return total
        else:
            return 1e6

    if by_num_uncovered:
        key_fn = num_uncovered_key
    elif by_percent_uncovered:
        key_fn = percent_uncovered_key
    else:
        key_fn = None  # default key, sort alphabetically

    return sorted(covdata, key=key_fn)


@contextmanager
def open_text_for_writing(filename=None, default_filename=None, **kwargs):
    """Context manager to open and close a file for text writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.endswith(os.sep):
        filename += default_filename

    if filename is not None and filename != "-":
        fh = open(filename, "w", **kwargs)
        close = True
    else:
        fh = sys.stdout
        close = False

    try:
        yield fh
    finally:
        if close:
            fh.close()


@contextmanager
def open_binary_for_writing(filename=None, default_filename=None, **kwargs):
    """Context manager to open and close a file for binary writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.endswith(os.sep):
        filename += default_filename

    if filename is not None and filename != "-":
        # files in write binary mode for UTF-8
        fh = open(filename, "wb", **kwargs)
        close = True
    else:
        fh = sys.stdout.buffer
        close = False

    try:
        yield fh
    finally:
        if close:
            fh.close()


def presentable_filename(filename, root_filter):
    # type: (str, re.Regex) -> str
    """mangle a filename so that it is suitable for a report"""

    normalized = root_filter.sub("", filename)
    if filename.endswith(normalized):
        # remove any slashes between the removed prefix and the normalized name
        if filename != normalized:
            while normalized.startswith(os.path.sep):
                normalized = normalized[len(os.path.sep) :]
    else:
        # Do no truncation if the filter does not start matching
        # at the beginning of the string
        normalized = filename

    return normalized.replace("\\", "/")
