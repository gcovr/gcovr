# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
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

# pylint: disable=too-many-lines

import logging
from typing import Any


LOGGER = logging.getLogger("gcovr")
SUSPICIOUS_COUNTER = 2**32


class UnknownLineType(Exception):
    """Used by `_parse_line()` to signal that no known line type matched."""

    def __init__(self, line: str) -> None:
        super().__init__(line)
        self.line = line


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
        """Raise exception if not ignored by options"""
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
        """Raise exception if not ignored by options"""
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
