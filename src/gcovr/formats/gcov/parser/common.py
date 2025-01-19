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

# pylint: disable=too-many-lines

import logging
from typing import Any


LOGGER = logging.getLogger("gcovr")
SUSPICIOUS_COUNTER = 2**32


class NegativeHits(Exception):
    """Used to signal that a negative count value was found."""

    def __init__(self, line: str) -> None:
        super().__init__(
            f"Got negative hit value in gcov line {line!r} caused by a\n"
            "bug in gcov tool, see\n"
            "https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option\n"
            "--gcov-ignore-parse-errors with a value of negative_hits.warn,\n"
            "or negative_hits.warn_once_per_file."
        )

    @staticmethod
    def raise_if_not_ignored(
        line: str, ignore_parse_errors: set[str], persistent_states: dict[str, Any]
    ) -> None:
        """
        Raise exception if not ignored by options
        >>> state = dict()
        >>> NegativeHits.raise_if_not_ignored("code", None, state)
        Traceback (most recent call last):
            ...
        gcovr.formats.gcov.parser.common.NegativeHits: Got negative hit value in gcov line 'code' caused by a
        bug in gcov tool, see
        https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option
        --gcov-ignore-parse-errors with a value of negative_hits.warn,
        or negative_hits.warn_once_per_file.
        >>> NegativeHits.raise_if_not_ignored("code", {"all"}, state)
        >>> state.get("negative_hits.warn_once_per_file")
        >>> NegativeHits.raise_if_not_ignored("code", {"negative_hits.warn"}, state)
        >>> state.get("negative_hits.warn_once_per_file")
        >>> NegativeHits.raise_if_not_ignored("code", {"negative_hits.warn_once_per_file"}, state)
        >>> state.get("negative_hits.warn_once_per_file")
        1
        >>> NegativeHits.raise_if_not_ignored("code", {"negative_hits.warn_once_per_file"}, state)
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
                LOGGER.warning(f"Ignoring negative hits in line {line!r}.")
                if "negative_hits.warn_once_per_file" in ignore_parse_errors:
                    persistent_states["negative_hits.warn_once_per_file"] = 1
        else:
            raise NegativeHits(line)


class SuspiciousHits(Exception):
    """Used to signal that a negative count value was found."""

    def __init__(self, line: str) -> None:
        super().__init__(
            f"Got suspicious hit value in gcov line {line!r} caused by a\n"
            "bug in gcov tool, see\n"
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
        Raise exception if not ignored by options
        >>> state = dict()
        >>> SuspiciousHits.raise_if_not_ignored("code", None, state)
        Traceback (most recent call last):
            ...
        gcovr.formats.gcov.parser.common.SuspiciousHits: Got suspicious hit value in gcov line 'code' caused by a
        bug in gcov tool, see
        https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option
        --gcov-ignore-parse-errors with a value of suspicious_hits.warn,
        or suspicious_hits.warn_once_per_file or change the threshold
        for the detection with option --gcov-suspicious-hits-threshold.
        >>> SuspiciousHits.raise_if_not_ignored("code", {"all"}, state)
        >>> state.get("suspicious_hits.warn_once_per_file")
        >>> SuspiciousHits.raise_if_not_ignored("code", {"suspicious_hits.warn"}, state)
        >>> state.get("suspicious_hits.warn_once_per_file")
        >>> SuspiciousHits.raise_if_not_ignored("code", {"suspicious_hits.warn_once_per_file"}, state)
        >>> state.get("suspicious_hits.warn_once_per_file")
        1
        >>> SuspiciousHits.raise_if_not_ignored("code", {"suspicious_hits.warn_once_per_file"}, state)
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
                LOGGER.warning(f"Ignoring suspicious hits in line {line!r}.")
                if "suspicious_hits.warn_once_per_file" in ignore_parse_errors:
                    persistent_states["suspicious_hits.warn_once_per_file"] = 1
        else:
            raise SuspiciousHits(line)


def check_hits(
    hits: int,
    line: str,
    ignore_parse_errors: set[str],
    suspicious_hits_threshold: int,
    persistent_states: dict[str, Any],
) -> int:
    """
    Check if hits count is negative or suspicious, if the issue is ignored returns 0
    >>> check_hits(1, "", {}, 10, {})
    1
    >>> check_hits(-1, "", {"all"}, 10, {})
    0
    >>> check_hits(1000, "", {"all"}, 10, {})
    0
    """
    if hits < 0:
        NegativeHits.raise_if_not_ignored(line, ignore_parse_errors, persistent_states)
        hits = 0

    if suspicious_hits_threshold != 0 and hits >= suspicious_hits_threshold:
        SuspiciousHits.raise_if_not_ignored(
            line, ignore_parse_errors, persistent_states
        )
        hits = 0

    return hits
