#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.8+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

"""Utility functions for gcovr."""

import functools
import gzip
import json
import lzma
import os
import re
import sys
from contextlib import contextmanager
from hashlib import md5
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Callable, Generator, Iterator, TextIO

from lxml import etree

from .exceptions import SanityCheckError
from .logging import LOGGER
from .version import __version__

if TYPE_CHECKING:
    from .filter import Filter

REGEX_VERSION_POSTFIX = re.compile(r"(.+?)(?:\.post\d+)?\.dev.+$")
PRETTY_JSON_INDENT = 4
GZIP_SUFFIX = ".gz"
LZMA_SUFFIX = ".xz"


class LoopChecker:
    """Class for checking if a directory was already scanned."""

    def __init__(self) -> None:
        """Initialize the loop checker."""
        self._seen = set[tuple[int, int]]()

    def already_visited(self, path: Path) -> bool:
        """Check if the path was already checked."""
        st = path.stat()
        key = (st.st_dev, st.st_ino)
        if key in self._seen:
            return True

        self._seen.add(key)
        return False


@functools.lru_cache(maxsize=1)
def is_fs_case_insensitive() -> bool:
    """Check if the file system is case insensitive."""
    cwd = Path.cwd()
    cwd_upper = Path(str(cwd).upper())
    cwd_lower = Path(str(cwd).lower())
    # Guessing if file system is case insensitive.
    # The working directory is not the root and accessible in upper and lower case
    # and pointing to same file.
    ret = (
        (str(cwd) != os.path.sep)
        and cwd_upper.exists()
        and cwd_lower.exists()
        and cwd_upper.samefile(cwd_lower)
    )
    LOGGER.debug("File system is case %s.", "insensitive" if ret else "sensitive")

    return ret


@functools.cache
def fix_case_of_path(path: Path) -> Path:
    """Fix casing of filenames for case insensitive file systems."""
    rest = path.parent
    cur = path.name
    # e.g path = ".." happens if original path is like "../dir/subdir/file.cpp"
    if not rest:
        return Path(cur)
    if not cur:  # e.g path = "C:/"
        return rest

    try:
        cur_lower = cur.lower()
        matched_filename = [f for f in rest.glob("*") if str(f).lower() == cur_lower]
        if len(matched_filename) > 1:
            msg = "Seems that we have a case sensitive filesystem, cannot fix file case"
            raise SanityCheckError(msg)

        if len(matched_filename) == 1:
            path = fix_case_of_path(rest) / matched_filename[0]
    except FileNotFoundError:
        LOGGER.warning("Cannot fix case of path because %s not found.", rest)

    return path


def get_version_for_report() -> str:
    """Get the printable version for the report."""
    version = __version__
    if match := REGEX_VERSION_POSTFIX.match(version):
        version = f"{match.group(1)}+main"
    return version


def search_file(
    predicate: Callable[[Path], bool],
    path: Path,
    exclude_directory: "tuple[Filter, ...]",
) -> Iterator[Path]:
    """Recursively descend path to find files that satisfy a predicate."""
    if str(path) == ".":
        path = Path.cwd()
    elif not path.exists():
        msg = f"Unknown directory '{path}'"
        raise OSError(msg)

    loop_checker = LoopChecker()
    for root, dirs, files in os.walk(path, followlinks=True):
        # Check if we've already visited 'root' through the magic of symlinks
        if loop_checker.already_visited(Path(root)):
            dirs[:] = []
            continue

        dirs[:] = [
            d
            for d in sorted(dirs)
            if not any(exc.match(Path(root) / d) for exc in exclude_directory)
        ]

        for filename in [(Path(root) / f) for f in sorted(files)]:
            if predicate(filename):
                yield filename.absolute()


def commonpath(files: list[Path]) -> Path:
    r"""
    Find the common prefix of all files.

    This differs from the standard library os.path.commonpath():
    - We first normalize all paths to a realpath.

    No common path exists under the following circumstances:
    - on Windows when the paths have different drives.
      E.g.: commonpath([r'C:\foo', r'D:\foo']) == ''
    - when the `files` are empty.

    Arguments:
        files (list): the input paths, may be relative or absolute.

    Returns: Path | None
        The common prefix directory as a relative path.
        Returns None if no common path exists.

    """
    if len(files) == 1:
        prefix_path = files[0].resolve().parent
    else:
        split_paths = [file.resolve().parts for file in files]
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
        prefix_path = Path(*common)

    LOGGER.debug("Common prefix path is '%s'.", prefix_path)

    # make the path relative
    if prefix_path:
        prefix_path = Path(os.path.relpath(prefix_path, Path.cwd()))
        LOGGER.debug("Common relative prefix path is '%s'.", prefix_path)
    return prefix_path


def normpath(path: Path) -> Path:
    """
    Normalize the given path.

    This differs from the standard library os.path.normpath():
    - We only normalize a .. if the parent is not a symbolic link.
    """
    path_parts = Path(path).absolute().parts
    path_normalized = Path(path_parts[0])
    if len(path_parts) > 1:
        for part in path_parts[1:]:
            if part == ".." and not path_normalized.is_symlink():
                path_normalized = path_normalized.parent
            else:
                path_normalized /= part
    return path_normalized


def relpath(path: Path, start: Path) -> Path:
    """Get the relative path with os.path.relpath."""
    return Path(os.path.relpath(path, start))


@contextmanager
def open_text_for_writing(
    filename: Path | None, default_filename: str | None = None, **kwargs: Any
) -> Generator[TextIO | Any, None, None]:
    """
    Context manager to open and close a file for text writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.is_dir():
        if default_filename is None:
            msg = "If filename is a directory a default filename is mandatory."
            raise AssertionError(msg)
        filename /= default_filename

    if filename is not None and str(filename) != "-":
        if filename.suffix == GZIP_SUFFIX:
            with gzip.open(filename, "wt", **kwargs) as fh_out:
                yield fh_out
        elif filename.suffix == LZMA_SUFFIX:
            with lzma.open(filename, "wt", **kwargs) as fh_out:
                yield fh_out
        else:
            with Path(filename).open("w", **kwargs) as fh_out:  # pylint: disable=unspecified-encoding
                yield fh_out
    else:
        encoding = kwargs.get("encoding", "utf-8").lower()
        old_encoding = sys.stdout.encoding
        try:
            if old_encoding != encoding:
                sys.stdout.reconfigure(encoding=encoding)  # type: ignore[union-attr]
            yield sys.stdout
        finally:
            if old_encoding != encoding:
                sys.stdout.reconfigure(encoding=old_encoding)  # type: ignore[union-attr]


@contextmanager
def open_binary_for_writing(
    filename: Path | None,
    default_filename: str,
    **kwargs: Any,
) -> Generator[BinaryIO | Any, None, None]:
    """
    Context manager to open and close a file for binary writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.is_dir():
        filename /= default_filename

    if filename is not None and str(filename) != "-":
        if filename.name.endswith(GZIP_SUFFIX):
            with gzip.open(filename, "wb", **kwargs) as fh_out:
                yield fh_out
        elif filename.name.endswith(LZMA_SUFFIX):
            with lzma.open(filename, "wb", **kwargs) as fh_out:
                yield fh_out
        else:
            # files in write binary mode for UTF-8
            with Path(filename).open("wb", **kwargs) as fh_out:
                yield fh_out
    else:
        yield sys.stdout.buffer


def write_json_output(
    json_dict: dict[str, Any],
    *,
    pretty: bool,
    filename: Path | None,
    default_filename: str,
    **kwargs: Any,
) -> None:
    """Write JSON dictionary to a file/STDOUT."""
    with open_text_for_writing(filename, default_filename, **kwargs) as fh:
        json.dump(
            json_dict,
            fh,
            indent=PRETTY_JSON_INDENT if pretty else None,
        )


def write_xml_output(
    root: Any,
    *,
    doctype: str | None = None,
    pretty: bool,
    filename: Path | None,
    default_filename: str,
    **kwargs: Any,
) -> None:
    """Write XML format dictionary to a file/STDOUT."""
    with open_binary_for_writing(filename, default_filename, **kwargs) as fh:
        fh.write(
            etree.tostring(
                root,
                pretty_print=pretty,
                encoding="utf-8",
                xml_declaration=True,
                doctype=doctype,  # type: ignore [arg-type]
            )
        )


@contextmanager
def chdir(directory: Path) -> Generator[None, None, None]:
    """Context for doing something in a locked directory."""
    current_dir = Path.cwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(current_dir)


def get_md5_hexdigest(data: bytes) -> str:
    """Get the MD5 digest of the given bytes."""
    return md5(data, usedforsecurity=False).hexdigest()  # nosec # Not used for security


def read_source_file(
    source_encoding: str, filename: Path, max_line_number: int
) -> list[str]:
    """Read in the source file and fill up lines if needed."""
    source_lines: list[bytes] = []
    try:
        source_lines = Path(filename).read_bytes().splitlines()
        lines = len(source_lines)
        if lines < max_line_number:
            LOGGER.warning(
                "File %s has %d line(s) but coverage data has %d line(s).",
                filename,
                lines,
                max_line_number,
            )
            # GCOV itself adds the /*EOF*/ in the text report if there is no data and we
            # used the same.
            source_lines += [b"/*EOF*/"] * (max_line_number - lines)
    except OSError as e:
        if filename.name == "<stdin>":
            message = (
                f"Got unreadable source file '{filename}', replacing with empty lines."
            )
            LOGGER.info(message)
        else:
            # The exception contains the source file name,
            # e.g. [Errno 2] No such file or directory: 'xy.txt'
            message = f"Cannot read file, using empty lines: {e}"
            LOGGER.warning(message)
            # If we cannot read the file we use as first line the error
            # and use empty lines for the rest of the lines.
        source_lines = [b""] * max_line_number
        source_lines[0] = f"/* {message} */".encode()

    return [line.decode(source_encoding, errors="replace") for line in source_lines]
