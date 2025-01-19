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

from hashlib import md5
from typing import Any, Callable, Iterator, Optional
import logging
import os
import functools
import re
import sys
from contextlib import contextmanager

from .version import __version__

LOGGER = logging.getLogger("gcovr")

REGEX_VERSION_POSTFIX = re.compile(r"(.+)\.dev.+$")


class LoopChecker:
    """Class for checking if a directory was already scanned."""

    def __init__(self) -> None:
        self._seen = set[tuple[int, int]]()

    def already_visited(self, path: str) -> bool:
        """Check if the path was already checked."""
        st = os.stat(path)
        key = (st.st_dev, st.st_ino)
        if key in self._seen:
            return True

        self._seen.add(key)
        return False


@functools.lru_cache(maxsize=1)
def is_fs_case_insensitive() -> bool:
    """Check if the file system is case insensitive."""
    cwd = os.getcwd()
    # Guessing if file system is case insensitive.
    # The working directory is not the root and accessible in upper and lower case
    # and pointing to same file.
    ret = (
        (cwd != os.path.sep)
        and os.path.exists(cwd.upper())
        and os.path.exists(cwd.lower())
        and os.path.samefile(cwd.upper(), cwd.lower())
    )
    LOGGER.debug(f"File system is case {'in' if ret else ''}sensitive.")

    return ret


@functools.lru_cache(maxsize=None)
def fix_case_of_path(path: str) -> str:
    """Fix casing of filenames for cas insensitive file systems."""
    rest, cur = os.path.split(path)
    # e.g path = ".." happens if original path is like "../dir/subdir/file.cpp"
    if not rest:
        return cur
    if not cur:  # e.g path = "C:/"
        return rest.upper()  # Always use uppercase drive letter

    try:
        cur_lower = cur.lower()
        matched_filename = [f for f in os.listdir(rest) if f.lower() == cur_lower]
        if len(matched_filename) > 1:
            raise RuntimeError(
                "Seems that we have a case sensitive filesystem, can't fix file case"
            )

        if len(matched_filename) == 1:
            path = os.path.join(fix_case_of_path(rest), matched_filename[0])
    except FileNotFoundError:
        LOGGER.warning(f"Can not fix case of path because {rest} not found.")

    return path.replace("\\", "/")


def get_version_for_report() -> str:
    """Get the printable version for the report."""
    version = __version__
    if match := REGEX_VERSION_POSTFIX.match(version):
        major, minor = match.group(1).split(".")
        version = f"{major}.{int(minor)-1}+main"
    return version


def search_file(
    predicate: Callable[[str], bool], path: str, exclude_dirs: list[re.Pattern[str]]
) -> Iterator[str]:
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
            for d in sorted(dirs)
            if not any(exc.match(os.path.join(root, d)) for exc in exclude_dirs)
        ]
        root = os.path.abspath(root)

        for name in sorted(files):
            if predicate(name):
                yield os.path.abspath(os.path.join(root, name))


def commonpath(files: list[str]) -> str:
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
        prefix_path = str(os.path.dirname(os.path.realpath(files[0])))
    else:
        split_paths = [os.path.realpath(path).split(os.path.sep) for path in files]
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

    LOGGER.debug(f"Common prefix path is {prefix_path!r}")

    # make the path relative and add a trailing slash
    if prefix_path:
        prefix_path = os.path.join(
            os.path.relpath(prefix_path, os.path.realpath(os.getcwd())), ""
        )
        LOGGER.debug(f"Common relative prefix path is {prefix_path!r}")
    return prefix_path


@contextmanager
def open_text_for_writing(
    filename: Optional[str], default_filename: Optional[str] = None, **kwargs: Any
) -> Iterator[Any]:
    """Context manager to open and close a file for text writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.endswith(os.sep):
        if default_filename is None:
            raise AssertionError(
                "If filename is a directory a default filename is mandatory."
            )
        filename += default_filename

    if filename is not None and filename != "-":
        with open(filename, "w", **kwargs) as fh_out:  # pylint: disable=unspecified-encoding
            yield fh_out
    else:
        yield sys.stdout


@contextmanager
def open_binary_for_writing(
    filename: Optional[str],
    default_filename: str,
    **kwargs: Any,
) -> Iterator[Any]:
    """Context manager to open and close a file for binary writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.endswith(os.sep):
        filename += default_filename

    if filename is not None and filename != "-":
        # files in write binary mode for UTF-8
        with open(filename, "wb", **kwargs) as fh_out:
            yield fh_out
    else:
        yield sys.stdout.buffer


@contextmanager
def chdir(directory: str) -> Iterator[None]:
    """Context for doing something in a locked directory."""
    current_dir = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(current_dir)


def force_unix_separator(path: str) -> str:
    """Get the filename with / independent from OS."""
    return path.replace("\\", "/")


def presentable_filename(filename: str, root_filter: re.Pattern[str]) -> str:
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

    return force_unix_separator(normalized)


def get_md5_hexdigest(data: bytes) -> str:
    """Get the MD5 digest of the given bytes."""
    return md5(data, usedforsecurity=False).hexdigest()  # nosec # Not used for security
