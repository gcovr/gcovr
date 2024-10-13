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

"""Utils for exclusion of lines and branches"""

import logging
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from ..coverage import FileCoverage, FunctionCoverage

LOGGER = logging.getLogger("gcovr")

ExclusionPredicate = Callable[[int], bool]
FunctionListByLine = Dict[int, List[FunctionCoverage]]


def function_exclude_not_supported(
    filename: Optional[str] = None,
    lineno: Optional[int] = None,
    columnno: Optional[int] = None,
) -> None:
    """warn that a function exclude isn't supported"""
    if filename is None:
        LOGGER.warning("Function exclusion not supported for this compiler.")
    else:
        LOGGER.warning(
            f"Function exclude marker found on line {lineno}:{columnno} but not supported for this compiler, "
            f"when processing {filename}."
        )


def function_exclude_not_at_function_line(
    filename: str, lineno: int, columnno: int
) -> None:
    """warn that a function exclude is found at a line where no function is defined"""
    LOGGER.warning(
        f"Function exclude marker found on line {lineno}:{columnno} but no function definition found, "
        f"when processing {filename}."
    )


def get_functions_by_line(filecov: FileCoverage) -> FunctionListByLine:
    """Get dict with the linenumber as key and the function defined in the line as value."""
    functions_by_line: FunctionListByLine = {}
    if filecov is not None:
        for function in filecov.functions.values():
            if function.start is not None:
                for lineno, _ in function.start.items():
                    if lineno not in functions_by_line:
                        functions_by_line[lineno] = []
                    functions_by_line[lineno].append(function)

    return functions_by_line


def get_function_exclude_ranges(
    filename: str, lineno: int, columnno: int, *, functions_by_line: FunctionListByLine
) -> List[Tuple[int, int]]:
    exclude_ranges = []
    if functions_by_line:
        lineno_end = None
        # Find the closest function definition in this line. Check end column if end line is on same line
        function_iter = iter(functions_by_line.get(lineno, []))
        for function in function_iter:
            if columnno > function.start[lineno][1] and (
                lineno < function.end[lineno][0] or columnno < function.end[lineno][1]
            ):
                lineno_end = function.end[lineno][0]
                break
        else:
            function_exclude_not_at_function_line(filename, lineno, columnno)

        if lineno_end is not None:
            included_ranges = []
            # Now we need to check for nested functions which are included
            for function in function_iter:
                included_ranges.append((lineno, function.end[lineno][0] + 1))
            for function_lineno in range(lineno + 1, lineno_end):
                for function in functions_by_line.get(function_lineno, []):
                    included_ranges.append(
                        (
                            function.start[function_lineno][0],
                            function.end[function_lineno][0],
                        )
                    )
            if included_ranges:
                last_include_end = lineno
                for include_start, include_end in included_ranges:
                    # The exclusion end must be in the line before
                    exclude_ranges.append((last_include_end, include_start - 1))
                    # The next exclusion must start after the included line
                    last_include_end = include_end + 1
                exclude_ranges.append((last_include_end, lineno_end))
            else:
                exclude_ranges.append((lineno, lineno_end))
    else:
        function_exclude_not_supported(filename, lineno, columnno)

    return exclude_ranges


def apply_exclusion_ranges(
    filecov: FileCoverage,
    *,
    line_is_excluded: ExclusionPredicate,
    branch_is_excluded: ExclusionPredicate,
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

    for linecov in filecov.lines.values():
        # always erase decision coverage since exclusions can change analysis
        linecov.decision = None

        if line_is_excluded(linecov.lineno):
            linecov.excluded = True
            linecov.branches = {}
            linecov.count = 0

        elif branch_is_excluded(linecov.lineno):
            linecov.branches = {}

    for function in filecov.functions.values():
        for lineno in function.excluded.keys():
            if line_is_excluded(lineno):
                function.count[lineno] = 0
                function.excluded[lineno] = True


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
