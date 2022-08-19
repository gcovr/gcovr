# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2022 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

"""
Handle exclusion markers.
"""

from typing import List, Optional, Callable, Tuple
import logging
import re

from .coverage import FileCoverage, LineCoverage


logger = logging.getLogger("gcovr")

_EXCLUDE_FLAG = "_EXCL_"
_EXCLUDE_LINE_WORD = ""
_EXCLUDE_BRANCH_WORD = "BR_"
_EXCLUDE_PATTERN_POSTFIX = "(LINE|START|STOP)"

ExclusionPredicate = Callable[[int], bool]


def apply_exclusions(
    filecov: FileCoverage,
    *,
    lines: List[Tuple[int, str]],
    exclude_lines_by_pattern: Optional[str],
    exclude_branches_by_pattern: Optional[str],
    exclude_pattern_prefix: str,
) -> FileCoverage:
    """
    Remove any coverage information that is excluded by explicit markers such as
    ``GCOVR_EXCL_LINE``.

    May modify/reuse the input FileCoverage.
    """

    line_is_excluded, branch_is_excluded = _find_excluded_ranges(
        lines=lines,
        warnings=_ExclusionRangeWarnings(filecov.filename),
        exclude_lines_by_custom_pattern=exclude_lines_by_pattern,
        exclude_branches_by_custom_pattern=exclude_branches_by_pattern,
        exclude_pattern_prefix=exclude_pattern_prefix,
    )

    _apply_exclusions_to_file(
        filecov,
        line_is_excluded=line_is_excluded,
        branch_is_excluded=branch_is_excluded,
    )

    return filecov


def _apply_exclusions_to_file(
    filecov: FileCoverage,
    *,
    line_is_excluded: ExclusionPredicate,
    branch_is_excluded: ExclusionPredicate,
) -> None:
    for linecov in filecov.lines.values():
        _apply_exclusions_to_line(
            linecov,
            line_is_excluded=line_is_excluded,
            branch_is_excluded=branch_is_excluded,
        )


def _apply_exclusions_to_line(
    linecov: LineCoverage,
    *,
    line_is_excluded: ExclusionPredicate,
    branch_is_excluded: ExclusionPredicate,
) -> None:
    # always erase decision coverage since exclusions can change analysis
    linecov.decision = None

    if line_is_excluded(linecov.lineno):
        linecov.excluded = True
        linecov.branches = {}
        linecov.count = 0
        return

    if branch_is_excluded(linecov.lineno):
        linecov.branches = {}


class _ExclusionRangeWarnings:
    r"""
    Log warnings related to exclusion marker processing.

    Example:
    >>> source = '''\
    ... 1: some code
    ... 2: foo // LCOV_EXCL_STOP
    ... 3: bar // GCOVR_EXCL_START
    ... 4: bar // GCOVR_EXCL_LINE
    ... 5: baz // GCOV_EXCL_STOP
    ... 6: "GCOVR_EXCL_START"
    ... '''
    >>> lines = []
    >>> for line in source.splitlines():
    ...   lineno, code = line.split(': ', maxsplit=1)
    ...   lines.append((int(lineno), code))
    >>> caplog = getfixture('caplog')
    >>> caplog.clear()
    >>> _ = apply_exclusions(  # doctest: +NORMALIZE_WHITESPACE
    ...     FileCoverage('example.cpp'),
    ...     lines=lines,
    ...     exclude_lines_by_pattern=None,
    ...     exclude_branches_by_pattern=None,
    ...     exclude_pattern_prefix='[GL]COVR?')
    >>> for message in caplog.record_tuples:
    ...     print(f"{message[1]}: {message[2]}")
    30: mismatched coverage exclusion flags.
              LCOV_EXCL_STOP found on line 2 without corresponding LCOV_EXCL_START, when processing example.cpp.
    30: GCOVR_EXCL_LINE found on line 4 in excluded region started on line 3, when processing example.cpp.
    30: GCOVR_EXCL_START found on line 3 was terminated by GCOV_EXCL_STOP on line 5, when processing example.cpp.
    30: The coverage exclusion region start flag GCOVR_EXCL_START
              on line 6 did not have corresponding GCOVR_EXCL_STOP flag
              in file example.cpp.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def mismatched_start_stop(
        self, start_lineno: int, start: str, stop_lineno: int, stop: str
    ) -> None:
        """warn that start/stop region markers don't match"""
        logger.warning(
            f"{start} found on line {start_lineno} "
            f"was terminated by {stop} on line {stop_lineno}, "
            f"when processing {self.filename}."
        )

    def stop_without_start(self, lineno: int, expected_start: str, stop: str) -> None:
        """warn that a region was ended without corresponding start marker"""
        logger.warning(
            "mismatched coverage exclusion flags.\n"
            f"          {stop} found on line {lineno} without corresponding {expected_start}, "
            f"when processing {self.filename}."
        )

    def start_without_stop(self, lineno: int, start: str, expected_stop: str) -> None:
        """warn that a region was started but not closed"""
        logger.warning(
            f"The coverage exclusion region start flag {start}\n"
            f"          on line {lineno} did not have corresponding {expected_stop} flag\n"
            f"          in file {self.filename}."
        )

    def line_after_start(self, lineno: int, start: str, start_lineno: int) -> None:
        """warn that a region was started but an excluded line was found"""
        logger.warning(
            f"{start} found on line {lineno} in excluded region started on line {start_lineno}, "
            f"when processing {self.filename}."
        )


def _process_exclusion_marker(
    lineno: int,
    flag: str,
    header: str,
    exclude_word: str,
    warnings: _ExclusionRangeWarnings,
    exclude_ranges: List[Tuple[int, int]],
    exclusion_stack: List[Tuple[str, int]],
) -> None:
    """
    Process the exclusion marker.

    Header is a marker name like LCOV or GCOVR.

    START flags are added to the exlusion stack
    STOP flags remove a marker from the exclusion stack
    """

    if flag == "LINE":
        if exclusion_stack:
            warnings.line_after_start(
                lineno,
                f"{header}" + _EXCLUDE_FLAG + exclude_word + "LINE",
                exclusion_stack[-1][1],
            )
        else:
            exclude_ranges.append((lineno, lineno))

    if flag == "START":
        exclusion_stack.append((header, lineno))

    elif flag == "STOP":
        if not exclusion_stack:
            warnings.stop_without_start(
                lineno,
                f"{header}" + _EXCLUDE_FLAG + exclude_word + "START",
                f"{header}" + _EXCLUDE_FLAG + exclude_word + "STOP",
            )
        else:
            start_header, start_lineno = exclusion_stack.pop()
            if header != start_header:
                warnings.mismatched_start_stop(
                    start_lineno,
                    f"{start_header}" + _EXCLUDE_FLAG + exclude_word + "START",
                    lineno,
                    f"{header}" + _EXCLUDE_FLAG + exclude_word + "STOP",
                )

            exclude_ranges.append((start_lineno, lineno))

    else:  # pragma: no cover
        pass


def _find_excluded_ranges(
    lines: List[Tuple[int, str]],
    *,
    warnings: _ExclusionRangeWarnings,
    exclude_lines_by_custom_pattern: Optional[str] = None,
    exclude_branches_by_custom_pattern: Optional[str] = None,
    exclude_pattern_prefix: str,
) -> Tuple[Callable[[int], bool], Callable[[int], bool]]:
    """
    Scan through all lines to find line ranges and branch ranges covered by exclusion markers.

    Example:
    >>> lines = [(11, '//PREFIX_EXCL_LINE'), (13, '//IGNORE_LINE'), (15, '//PREFIX_EXCL_START'), (18, '//PREFIX_EXCL_STOP'),
    ...     (21, '//PREFIX_EXCL_BR_LINE'), (23, '//IGNORE_BR'), (25, '//PREFIX_EXCL_BR_START'), (28, '//PREFIX_EXCL_BR_STOP')]
    >>> exclude_line, exclude_branch = _find_excluded_ranges(
    ...     lines, warnings=..., exclude_lines_by_custom_pattern = '.*IGNORE_LINE',
    ...     exclude_branches_by_custom_pattern = '.*IGNORE_BR', exclude_pattern_prefix='PREFIX')
    >>> [lineno for lineno in range(30) if exclude_line(lineno)]
    [11, 13, 15, 16, 17, 18]
    >>> [lineno for lineno in range(30) if exclude_branch(lineno)]
    [21, 23, 25, 26, 27, 28]

    The stop marker line is inclusive:
    >>> exclude_line, _ = _find_excluded_ranges(
    ...     [(3, '// PREFIX_EXCL_START'),
    ...      (6, '// PREFIX_EXCL_STOP')],
    ...     warnings=...,
    ...     exclude_pattern_prefix='PREFIX')
    >>> for lineno in range(1, 10):
    ...     print(f"{lineno}: {'excluded' if exclude_line(lineno) else 'code'}")
    1: code
    2: code
    3: excluded
    4: excluded
    5: excluded
    6: excluded
    7: code
    8: code
    9: code
    """
    exclude_lines_by_custom_pattern_regex = None
    if exclude_lines_by_custom_pattern:
        exclude_lines_by_custom_pattern_regex = re.compile(
            exclude_lines_by_custom_pattern
        )

    exclude_branches_by_custom_pattern_regex = None
    if exclude_branches_by_custom_pattern:
        exclude_branches_by_custom_pattern_regex = re.compile(
            exclude_branches_by_custom_pattern
        )

    # possibly overlapping half-open ranges that are excluded
    exclude_line_ranges: List[Tuple[int, int]] = []
    exclude_branch_ranges: List[Tuple[int, int]] = []

    exclusion_stack_line = []
    exclusion_stack_branch = []

    excl_line_pattern = None
    excl_branch_pattern = None
    for lineno, code in lines:
        # line marker exclusion
        if _EXCLUDE_FLAG in code:
            if excl_line_pattern is None:
                excl_line_pattern = re.compile(
                    "("
                    + exclude_pattern_prefix
                    + ")"
                    + _EXCLUDE_FLAG
                    + _EXCLUDE_LINE_WORD
                    + _EXCLUDE_PATTERN_POSTFIX
                )

            for header, flag in excl_line_pattern.findall(code):
                _process_exclusion_marker(
                    lineno,
                    flag,
                    header,
                    _EXCLUDE_LINE_WORD,
                    warnings,
                    exclude_line_ranges,
                    exclusion_stack_line,
                )

        if exclude_lines_by_custom_pattern_regex:
            if exclude_lines_by_custom_pattern_regex.match(code):
                exclude_line_ranges.append((lineno, lineno))

        # branch marker exclusion
        if _EXCLUDE_FLAG in code:
            if excl_branch_pattern is None:
                excl_branch_pattern = re.compile(
                    "("
                    + exclude_pattern_prefix
                    + ")"
                    + _EXCLUDE_FLAG
                    + _EXCLUDE_BRANCH_WORD
                    + _EXCLUDE_PATTERN_POSTFIX
                )
            for header, flag in excl_branch_pattern.findall(code):
                _process_exclusion_marker(
                    lineno,
                    flag,
                    header,
                    _EXCLUDE_BRANCH_WORD,
                    warnings,
                    exclude_branch_ranges,
                    exclusion_stack_branch,
                )

        if exclude_branches_by_custom_pattern_regex:
            if exclude_branches_by_custom_pattern_regex.match(code):
                exclude_branch_ranges.append((lineno, lineno))

    for header, lineno in exclusion_stack_line:
        warnings.start_without_stop(
            lineno,
            f"{header}" + _EXCLUDE_FLAG + _EXCLUDE_LINE_WORD + "START",
            f"{header}" + _EXCLUDE_FLAG + _EXCLUDE_LINE_WORD + "STOP",
        )

    for header, lineno in exclusion_stack_branch:
        warnings.start_without_stop(
            lineno,
            f"{header}" + _EXCLUDE_FLAG + _EXCLUDE_BRANCH_WORD + "START",
            f"{header}" + _EXCLUDE_FLAG + _EXCLUDE_BRANCH_WORD + "STOP",
        )

    return (
        _make_is_in_any_range_inclusive(exclude_line_ranges),
        _make_is_in_any_range_inclusive(exclude_branch_ranges),
    )


def _make_is_in_any_range_inclusive(
    ranges: List[Tuple[int, int]],
) -> Callable[[int], bool]:
    """
    Create a function to check whether an input is in any range (inclusive).

    This function should provide reasonable performance
    if queries are mostly made in ascending order.

    Example:
    >>> select = _make_is_in_any_range_inclusive([(3,3), (5,7)])
    >>> select(0)
    False
    >>> select(6)
    True
    >>> [x for x in range(10) if select(x)]
    [3, 5, 6, 7]
    """

    # values are likely queried in ascending order,
    # allowing the search to start with the first possible range
    ranges = sorted(ranges)
    hint_value = 0
    hint_index = 0

    def is_in_any_range(value: int) -> bool:
        nonlocal hint_value, hint_index

        # if the heuristic failed, restart search from the beginning
        if value < hint_value:
            hint_index = 0

        hint_value = value

        for i in range(hint_index, len(ranges)):
            start, end = ranges[i]
            hint_index = i

            # stop as soon as a too-large range is seen
            if value < start:
                break

            if start <= value <= end:
                return True
        else:
            hint_index = len(ranges)

        return False

    return is_in_any_range
