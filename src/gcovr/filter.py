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

import logging
import platform
import re
import os

from .utils import force_unix_separator, is_fs_case_insensitive

LOGGER = logging.getLogger("gcovr")


class Filter:
    """Base class for a filename filter."""

    def __init__(self, pattern: str) -> None:
        flags = re.IGNORECASE if is_fs_case_insensitive() else 0
        self.pattern = re.compile(pattern, flags)

    def match(self, path: str) -> bool:
        """Return True if the given path (always with /) matches the regular expression."""
        os_independent_path = force_unix_separator(path)
        if self.pattern.match(os_independent_path):
            LOGGER.debug(f"  Filter {self} matched for path {os_independent_path}.")
            return True
        return False

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.pattern.pattern})"


class AbsoluteFilter(Filter):
    """Class for a filename filter which matches against the real path of a file."""

    def match(self, path: str) -> bool:
        """Return True if the given path with all symlinks resolved matches the filter."""
        path = os.path.realpath(path)
        return super().match(path)


class RelativeFilter(Filter):
    """Class for a filename filter which matches against the relative paths of a file."""

    def __init__(self, root: str, pattern: str) -> None:
        super().__init__(pattern)
        self.root = os.path.realpath(root)

    def match(self, path: str) -> bool:
        """Return True if the given path with all symlinks resolved matches the filter."""
        path = os.path.realpath(path)

        # On Windows, a relative path can never cross drive boundaries.
        # If so, the relative filter cannot match.
        if platform.system() == "Windows":
            path_drive, _ = os.path.splitdrive(path)
            root_drive, _ = os.path.splitdrive(self.root)
            if path_drive != root_drive:  # pragma: no cover
                return False

        relpath = os.path.relpath(path, self.root)
        return super().match(relpath)

    def __str__(self) -> str:
        return f"RelativeFilter({self.pattern.pattern} root={self.root})"


class AlwaysMatchFilter(Filter):
    """Class for a filter which matches for all files."""

    def __init__(self) -> None:
        super().__init__("")

    def match(self, path: str) -> bool:
        """Return always True."""
        return True


class DirectoryPrefixFilter(Filter):
    """Class for a filename filter which matches for all files in a directory."""

    def __init__(self, directory: str) -> None:
        os_independent_path = force_unix_separator(directory)
        pattern = re.escape(f"{os_independent_path}/")
        super().__init__(pattern)

    def match(self, path: str) -> bool:
        """Return True if the given path matches the filter."""
        path = os.path.normpath(path)
        return super().match(path)


def is_file_excluded(
    filename: str,
    include_filters: list[Filter],
    exclude_filters: list[Filter],
) -> bool:
    """Apply inclusion/exclusion filters to filename.

    The include_filters are tested against
    the given (relative) filename.
    The exclude_filters are tested against
    the stripped, given (relative), and absolute filenames.

    filename (str): the absolute file path to match
    include_filters (list of FilterOption): ANY of these filters must match
    exclude_filters (list of FilterOption): NONE of these filters must match

    returns:
        True when filename is not matching a include filter or matches an exclude filter.
    """

    LOGGER.debug(f"Check if {filename} is included...")
    if not any(f.match(filename) for f in include_filters):
        LOGGER.debug("  No filter matched.")
        return True

    if not exclude_filters:
        return False

    LOGGER.debug("Check for exclusion...")
    if any(f.match(filename) for f in exclude_filters):
        return True

    LOGGER.debug("  No filter matched.")
    return False
