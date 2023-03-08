# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

"""
Handle explicit exclusion markers in source code, e.g. ``GCOVR_EXCL_LINE``.
"""

from typing import List, Optional, Tuple, Callable, Iterable
import logging
import re

from ..coverage import FileCoverage

logger = logging.getLogger("gcovr")

_EXCLUDE_FLAG = "_EXCL_"
_EXCLUDE_LINE_WORD = ""
_EXCLUDE_BRANCH_WORD = "BR_"
_EXCLUDE_PATTERN_POSTFIX = "(LINE|START|STOP)"

ExclusionPredicate = Callable[[int], bool]


def apply_exclusion_markers(
    filecov: FileCoverage,
    *,
    lines: List[str],
    exclude_lines_by_pattern: Optional[str],
    exclude_branches_by_pattern: Optional[str],
    exclude_pattern_prefix: str,
) -> None:
    """
    Remove any coverage information that is excluded by explicit markers such as
    ``GCOVR_EXCL_LINE``.

    Modifies the input FileCoverage in place.

    Arguments:
        filecov: the coverage to filter
        lines: the source code lines (not raw gcov lines)
        exclude_lines_by_pattern: string with regex syntax to exclude
            individual lines
        exclude_branches_by_pattern: string with regex syntax to exclude
            individual branches
        exclude_pattern_prefix: string with prefix for _LINE/_START/_STOP markers.
    """

    line_is_excluded, branch_is_excluded = _find_excluded_ranges(
        lines=lines,
        warnings=_ExclusionRangeWarnings(filecov.filename),
        exclude_lines_by_custom_pattern=exclude_lines_by_pattern,
        exclude_branches_by_custom_pattern=exclude_branches_by_pattern,
        exclude_pattern_prefix=exclude_pattern_prefix,
    )

    for linecov in filecov.lines.values():
        # always erase decision coverage since exclusions can change analysis
        linecov.decision = None

        if line_is_excluded(linecov.lineno):
            linecov.excluded = True
            linecov.branches = {}
            linecov.count = 0

        elif branch_is_excluded(linecov.lineno):
            linecov.branches = {}

    for functioncov in filecov.functions.values():
        for lineno in functioncov.excluded.keys():
            if line_is_excluded(lineno):
                functioncov.count[lineno] = 0
                functioncov.excluded[lineno] = True


class _ExclusionRangeWarnings:
    r"""
    Log warnings related to exclusion marker processing.

    Example:
    >>> source = '''\
    ... some code
    ... foo // LCOV_EXCL_STOP
    ... bar // GCOVR_EXCL_START
    ... bar // GCOVR_EXCL_LINE
    ... baz // GCOV_EXCL_STOP
    ... "GCOVR_EXCL_START"
    ... '''
    >>> caplog = getfixture('caplog')
    >>> caplog.clear()
    >>> _ = apply_exclusion_markers(  # doctest: +NORMALIZE_WHITESPACE
    ...     FileCoverage('example.cpp'),
    ...     lines=source.strip().splitlines(),
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
                f"{header}{_EXCLUDE_FLAG}{exclude_word}LINE",
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
                f"{header}{_EXCLUDE_FLAG}{exclude_word}START",
                f"{header}{_EXCLUDE_FLAG}{exclude_word}STOP",
            )
        else:
            start_header, start_lineno = exclusion_stack.pop()
            if header != start_header:
                warnings.mismatched_start_stop(
                    start_lineno,
                    f"{start_header}{_EXCLUDE_FLAG}{exclude_word}START",
                    lineno,
                    f"{header}{_EXCLUDE_FLAG}{exclude_word}STOP",
                )

            exclude_ranges.append((start_lineno, lineno - 1))

    else:  # pragma: no cover
        pass


def _find_excluded_ranges(
    lines: List[str],
    *,
    warnings: _ExclusionRangeWarnings,
    exclude_lines_by_custom_pattern: Optional[str] = None,
    exclude_branches_by_custom_pattern: Optional[str] = None,
    exclude_pattern_prefix: str,
) -> Tuple[ExclusionPredicate, ExclusionPredicate]:
    """
    Scan through all lines to find line ranges and branch ranges covered by exclusion markers.

    Example:
    >>> lines = [
    ...     (11, '//PREFIX_EXCL_LINE'), (13, '//IGNORE_LINE'),
    ...     (15, '//PREFIX_EXCL_START'), (18, '//PREFIX_EXCL_STOP'),
    ...     (21, '//PREFIX_EXCL_BR_LINE'), (23, '//IGNORE_BR'),
    ...     (25, '//PREFIX_EXCL_BR_START'), (28, '//PREFIX_EXCL_BR_STOP')]
    >>> exclude_line, exclude_branch = _find_excluded_ranges(
    ...     _lines_from_sparse(lines), warnings=...,
    ...     exclude_lines_by_custom_pattern='.*IGNORE_LINE',
    ...     exclude_branches_by_custom_pattern='.*IGNORE_BR',
    ...     exclude_pattern_prefix='PREFIX')
    >>> [lineno for lineno in range(30) if exclude_line(lineno)]
    [11, 13, 15, 16, 17]
    >>> [lineno for lineno in range(30) if exclude_branch(lineno)]
    [21, 23, 25, 26, 27]

    The stop marker line is NOT inclusive:
    >>> exclude_line, _ = _find_excluded_ranges(
    ...     _lines_from_sparse([(3, '// PREFIX_EXCL_START'), (7, '// PREFIX_EXCL_STOP')]),
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

    def find_range_impl(
        custom_pattern: Optional[str],
        exclude_word: str,
    ) -> ExclusionPredicate:
        custom_pattern_regex = None
        if custom_pattern:
            custom_pattern_regex = re.compile(custom_pattern)

        excl_pattern = re.compile(
            f"({exclude_pattern_prefix}){_EXCLUDE_FLAG}{exclude_word}{_EXCLUDE_PATTERN_POSTFIX}"
        )

        # possibly overlapping inclusive (closed) ranges that describe exclusions regions
        exclude_ranges: List[Tuple[int, int]] = []
        exclusion_stack: List[Tuple[str, int]] = []

        for lineno, code in enumerate(lines, 1):
            if _EXCLUDE_FLAG in code:
                for header, flag in excl_pattern.findall(code):
                    _process_exclusion_marker(
                        lineno,
                        flag,
                        header,
                        exclude_word,
                        warnings,
                        exclude_ranges,
                        exclusion_stack,
                    )

            if custom_pattern_regex:
                if custom_pattern_regex.match(code):
                    exclude_ranges.append((lineno, lineno))

        for header, lineno in exclusion_stack:
            warnings.start_without_stop(
                lineno,
                f"{header}{_EXCLUDE_FLAG}{exclude_word}START",
                f"{header}{_EXCLUDE_FLAG}{exclude_word}STOP",
            )

        return _make_is_in_any_range_inclusive(exclude_ranges)

    return (
        find_range_impl(exclude_lines_by_custom_pattern, _EXCLUDE_LINE_WORD),
        find_range_impl(exclude_branches_by_custom_pattern, _EXCLUDE_BRANCH_WORD),
    )


def _make_is_in_any_range_inclusive(
    ranges: List[Tuple[int, int]],
) -> ExclusionPredicate:
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


def _lines_from_sparse(sparse: Iterable[Tuple[int, str]]) -> List[str]:
    """
    Convert lineno–source tuples to a flat list, useful for tests.

    >>> _lines_from_sparse([(3, 'foo'), (2, 'bar'), (3, 'foo2')])
    ['', 'bar', 'foo2']
    """
    lines: List[str] = []
    for lineno, source in sparse:
        lines.extend("" for _ in range(len(lines), lineno))
        lines[lineno - 1] = source
    return lines
