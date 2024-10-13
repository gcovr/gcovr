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

from __future__ import annotations
from argparse import ArgumentTypeError
from hashlib import md5
from typing import Callable, List, Type
import logging
import os
import functools
import platform
import re
import sys
from contextlib import contextmanager
from colorlog import ColoredFormatter
from gcovr.options import Options

LOGGER = logging.getLogger("gcovr")
DEFAULT_LOGGING_HANDLER = logging.StreamHandler(sys.stderr)


LOG_FORMAT = "(%(levelname)s) %(message)s"
LOG_FORMAT_THREADS = "(%(levelname)s) - %(threadName)s - %(message)s"
COLOR_LOG_FORMAT = f"%(log_color)s{LOG_FORMAT}"
COLOR_LOG_FORMAT_THREADS = f"%(log_color)s{LOG_FORMAT_THREADS}"


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


@functools.lru_cache(maxsize=1)
def is_fs_case_insensitive():
    cwd = os.getcwd()
    # Guessing if file system is case insensitive.
    # The working directory is not the root and accessible in upper and lower case.
    ret = (
        (cwd != os.path.sep)
        and os.path.exists(cwd.upper())
        and os.path.exists(cwd.lower())
    )
    LOGGER.debug(f"File system is case {'in' if ret else ''}sensitive.")

    return ret


@functools.lru_cache(maxsize=None)
def fix_case_of_path(path: str):
    rest, cur = os.path.split(path)
    # e.g path = ".." happens if original path is like "../dir/subdir/file.cpp"
    if not rest:
        return cur
    if not cur:  # e.g path = "C:/"
        return rest.upper()  # Always use uppercase drive letter

    curL = cur.lower()
    matchedFileName = [f for f in os.listdir(rest) if f.lower() == curL]
    if len(matchedFileName) > 1:
        raise RuntimeError(
            "Seems that we have a case sensitive filesystem, can't fix file case"
        )

    if len(matchedFileName) == 1:
        path = os.path.join(fix_case_of_path(rest), matchedFileName[0])

    return path.replace("\\", "/")


def get_os_independent_path(path):
    return path.replace(os.path.sep, "/")


def search_file(
    predicate: Callable[[str], bool], path: str, exclude_dirs: List[re.Pattern]
):
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
        prefix_path = os.path.dirname(os.path.realpath(files[0]))
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
            LOGGER.warning("filters must use forward slashes as path separators")
            LOGGER.warning(f"your filter : {self.regex}")
            LOGGER.warning(f"did you mean: {suggestion}")

        isabs = self.regex.startswith("/")
        if not isabs and (platform.system() == "Windows"):
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
    def __init__(self, pattern: str):
        flags = re.IGNORECASE if is_fs_case_insensitive() else 0
        self.pattern = re.compile(pattern, flags)

    def match(self, path: str):
        os_independent_path = get_os_independent_path(path)
        return self.pattern.match(os_independent_path)

    def __str__(self):
        return "{name}({pattern})".format(
            name=type(self).__name__, pattern=self.pattern.pattern
        )


class AbsoluteFilter(Filter):
    def match(self, path: str):
        path = os.path.realpath(path)
        return super().match(path)


class RelativeFilter(Filter):
    def __init__(self, root: str, pattern: str):
        super().__init__(pattern)
        self.root = os.path.realpath(root)

    def match(self, path: str):
        path = os.path.realpath(path)

        # On Windows, a relative path can never cross drive boundaries.
        # If so, the relative filter cannot match.
        if platform.system() == "Windows":
            path_drive, _ = os.path.splitdrive(path)
            root_drive, _ = os.path.splitdrive(self.root)
            if path_drive != root_drive:
                return None

        relpath = os.path.relpath(path, self.root)
        return super().match(relpath)

    def __str__(self):
        return "RelativeFilter({} root={})".format(self.pattern.pattern, self.root)


class AlwaysMatchFilter(Filter):
    def __init__(self):
        super().__init__("")

    def match(self, path):
        return True


class DirectoryPrefixFilter(Filter):
    def __init__(self, directory):
        os_independent_path = get_os_independent_path(directory)
        pattern = re.escape(f"{os_independent_path}/")
        super().__init__(pattern)

    def match(self, path: str):
        path = os.path.normpath(path)
        return super().match(path)


def __colored_formatter(options: Options = None) -> ColoredFormatter:
    if options is not None:
        log_format = (
            COLOR_LOG_FORMAT_THREADS if options.gcov_parallel > 1 else COLOR_LOG_FORMAT
        )
        force_color = getattr(options, "force_color", False)
        no_color = getattr(options, "no_color", False)
    else:
        log_format = COLOR_LOG_FORMAT
        force_color = False
        no_color = False

    return ColoredFormatter(
        log_format,
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
        force_color=force_color,
        no_color=no_color,
        stream=sys.stderr,
    )


def configure_logging() -> None:
    """Configure the logging module"""
    DEFAULT_LOGGING_HANDLER.setFormatter(__colored_formatter())
    logging.basicConfig(level=logging.INFO, handlers=[DEFAULT_LOGGING_HANDLER])
    ci_logging_prefixes = None
    if "TF_BUILD" in os.environ:
        ci_logging_prefixes = {
            logging.WARNING: "##vso[task.logissue type=warning]",
            logging.ERROR: "##vso[task.logissue type=error]",
        }
    elif "GITHUB_ACTIONS" in os.environ:
        ci_logging_prefixes = {
            logging.WARNING: "::warning::",
            logging.ERROR: "::error::",
        }

    if ci_logging_prefixes is not None:

        class CiFormatter(logging.Formatter):
            """Formatter to format messages to be captured in Azure"""

            def __init__(self):
                super(CiFormatter, self).__init__(fmt=LOG_FORMAT)

            def format(self, record):
                if record.levelno in ci_logging_prefixes:
                    result = (
                        f"{ci_logging_prefixes[record.levelno]}{super().format(record)}"
                    )
                else:
                    result = ""

                return result

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(CiFormatter())
        logging.getLogger().addHandler(handler)

    def exception_hook(exc_type, exc_value, exc_traceback) -> None:
        logging.exception(
            "Uncaught EXCEPTION", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = exception_hook


def update_logging(options: Options) -> None:
    if options.verbose:
        LOGGER.setLevel(logging.DEBUG)

    # Update the formatter of the default logger depending on options
    DEFAULT_LOGGING_HANDLER.setFormatter(__colored_formatter(options))


@contextmanager
def open_text_for_writing(filename=None, default_filename=None, **kwargs):
    """Context manager to open and close a file for text writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.endswith(os.sep):
        filename += default_filename

    if filename is not None and filename != "-":
        with open(filename, "w", **kwargs) as fh_out:
            yield fh_out
    else:
        yield sys.stdout


@contextmanager
def open_binary_for_writing(filename=None, default_filename=None, **kwargs):
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
def chdir(dir_):
    """
    Context for doing something in a locked directory
    """
    current_dir = os.getcwd()
    os.chdir(dir_)
    try:
        yield
    finally:
        os.chdir(current_dir)


def force_unix_separator(path: str) -> str:
    return path.replace("\\", "/")


def presentable_filename(filename: str, root_filter: re.Pattern) -> str:
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
    return (
        md5(data, usedforsecurity=False)  # nosec # Not used for security
        if sys.version_info >= (3, 9)
        else md5(data)  # nosec # usedforsecurity not available in older versions
    ).hexdigest()
