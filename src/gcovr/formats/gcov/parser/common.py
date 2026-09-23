#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
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

"""GCOVR GCOV parser common functionality for JSON end text format of GCOV."""

# pylint: disable=too-many-lines

from typing import Any

from ....logging import LOGGER

SUSPICIOUS_COUNTER = 2**32


class NegativeHitsError(Exception):
    """Used to signal that a negative count value was found."""

    def __init__(self, line: str, persistent_states: dict[str, Any]) -> None:
        """Initialize negative hits error."""
        super().__init__(
            f"{':'.join(str(item) for item in persistent_states['location'])} Got negative hit value in: {line}\n"
            "This is caused by a bug in gcov tool, see\n"
            "https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option\n"
            "--gcov-ignore-parse-errors with a value of negative_hits.warn,\n"
            "or negative_hits.warn_once_per_file."
        )

    @staticmethod
    def raise_if_not_ignored(
        line: str, ignore_parse_errors: set[str], persistent_states: dict[str, Any]
    ) -> None:
        """
        Raise exception if not ignored by options.

        Examples:
        >>> state = {"location": ("file", 5)}
        >>> NegativeHitsError.raise_if_not_ignored("code with space", None, state)
        Traceback (most recent call last):
            ...
        gcovr.formats.gcov.parser.common.NegativeHitsError: file:5 Got negative hit value in: code with space
        This is caused by a bug in gcov tool, see
        https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option
        --gcov-ignore-parse-errors with a value of negative_hits.warn,
        or negative_hits.warn_once_per_file.
        >>> NegativeHitsError.raise_if_not_ignored("code", {"all"}, state)
        >>> state.get("negative_hits.warn_once_per_file")
        >>> NegativeHitsError.raise_if_not_ignored("code", {"negative_hits.warn"}, state)
        >>> state.get("negative_hits.warn_once_per_file")
        >>> NegativeHitsError.raise_if_not_ignored("code", {"negative_hits.warn_once_per_file"}, state)
        >>> state.get("negative_hits.warn_once_per_file")
        1
        >>> NegativeHitsError.raise_if_not_ignored("code", {"negative_hits.warn_once_per_file"}, state)
        >>> state.get("negative_hits.warn_once_per_file")
        2

        """
        if ignore_parse_errors is not None and any(
            v in ignore_parse_errors
            for v in [
                "all",
                "negative_hits.warn",
                "negative_hits.warn_once_per_file",
            ]
        ):
            if "negative_hits.warn_once_per_file" in persistent_states:
                persistent_states["negative_hits.warn_once_per_file"] += 1
            else:
                LOGGER.warning(
                    "%s: Ignoring negative hits in: %s.",
                    ":".join(str(item) for item in persistent_states["location"]),
                    line,
                )
                if "negative_hits.warn_once_per_file" in ignore_parse_errors:
                    persistent_states["negative_hits.warn_once_per_file"] = 1
        else:
            raise NegativeHitsError(line, persistent_states)


class SuspiciousHitsError(Exception):
    """Used to signal that a negative count value was found."""

    def __init__(self, line: str, persistent_states: dict[str, Any]) -> None:
        """Initialize suspicious hits error."""
        super().__init__(
            f"{':'.join(str(item) for item in persistent_states['location'])} Got suspicious hit value in: {line}\n"
            "This is caused by a bug in gcov tool, see\n"
            "https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option\n"
            "--gcov-ignore-parse-errors with a value of suspicious_hits.warn,\n"
            "or suspicious_hits.warn_once_per_file or change the threshold\n"
            "for the detection with option --gcov-suspicious-hits-threshold."
        )

    @staticmethod
    def raise_if_not_ignored(
        line: str, ignore_parse_errors: set[str], persistent_states: dict[str, Any]
    ) -> None:
        """
        Raise exception if not ignored by options.

        Examples:
        >>> state = dict(location=("file", 5))
        >>> SuspiciousHitsError.raise_if_not_ignored("code with space", None, state)
        Traceback (most recent call last):
            ...
        gcovr.formats.gcov.parser.common.SuspiciousHitsError: file:5 Got suspicious hit value in: code with space
        This is caused by a bug in gcov tool, see
        https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option
        --gcov-ignore-parse-errors with a value of suspicious_hits.warn,
        or suspicious_hits.warn_once_per_file or change the threshold
        for the detection with option --gcov-suspicious-hits-threshold.
        >>> SuspiciousHitsError.raise_if_not_ignored("code", {"all"}, state)
        >>> state.get("suspicious_hits.warn_once_per_file")
        >>> SuspiciousHitsError.raise_if_not_ignored("code", {"suspicious_hits.warn"}, state)
        >>> state.get("suspicious_hits.warn_once_per_file")
        >>> SuspiciousHitsError.raise_if_not_ignored("code", {"suspicious_hits.warn_once_per_file"}, state)
        >>> state.get("suspicious_hits.warn_once_per_file")
        1
        >>> SuspiciousHitsError.raise_if_not_ignored("code", {"suspicious_hits.warn_once_per_file"}, state)
        >>> state.get("suspicious_hits.warn_once_per_file")
        2

        """
        if ignore_parse_errors is not None and any(
            v in ignore_parse_errors
            for v in [
                "all",
                "suspicious_hits.warn",
                "suspicious_hits.warn_once_per_file",
            ]
        ):
            if "suspicious_hits.warn_once_per_file" in persistent_states:
                persistent_states["suspicious_hits.warn_once_per_file"] += 1
            else:
                LOGGER.warning(
                    "Ignoring suspicious hits in %s: %s.",
                    ":".join(str(item) for item in persistent_states["location"]),
                    line,
                )
                if "suspicious_hits.warn_once_per_file" in ignore_parse_errors:
                    persistent_states["suspicious_hits.warn_once_per_file"] = 1
        else:
            raise SuspiciousHitsError(line, persistent_states)


def check_hits(
    hits: int,
    line: str,
    ignore_parse_errors: set[str],
    suspicious_hits_threshold: int,
    persistent_states: dict[str, Any],
) -> int:
    """
    Check if hits count is negative or suspicious, if the issue is ignored returns 0.

    Examples:
    >>> check_hits(1, "code", {}, 10, {})
    1
    >>> check_hits(-1, "code with space", {}, 10, {"location": ("file", 5)})
    Traceback (most recent call last):
        ...
    gcovr.formats.gcov.parser.common.NegativeHitsError: file:5 Got negative hit value in: code with space
    This is caused by a bug in gcov tool, see
    https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option
    --gcov-ignore-parse-errors with a value of negative_hits.warn,
    or negative_hits.warn_once_per_file.
    >>> check_hits(1000, "code with space", {}, 10, {"location": ("file", 5)})
    Traceback (most recent call last):
        ...
    gcovr.formats.gcov.parser.common.SuspiciousHitsError: file:5 Got suspicious hit value in: code with space
    This is caused by a bug in gcov tool, see
    https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option
    --gcov-ignore-parse-errors with a value of suspicious_hits.warn,
    or suspicious_hits.warn_once_per_file or change the threshold
    for the detection with option --gcov-suspicious-hits-threshold.
    >>> check_hits(-1, "code", {"all"}, 10, {"location": ("file", 5)})
    0
    >>> check_hits(1000, "code", {"all"}, 10, {"location": ("file", 5)})
    0

    """
    if hits < 0:
        NegativeHitsError.raise_if_not_ignored(
            line, ignore_parse_errors, persistent_states
        )
        hits = 0

    if suspicious_hits_threshold != 0 and hits >= suspicious_hits_threshold:
        SuspiciousHitsError.raise_if_not_ignored(
            line, ignore_parse_errors, persistent_states
        )
        hits = 0

    return hits
