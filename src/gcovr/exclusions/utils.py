#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.8, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.8
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

"""Utils for exclusion of lines and branches."""

from typing import Callable, Iterable

from ..data_model.coverage import CodeRegion, FileCoverage, FunctionCoverage
from ..logging import LOGGER

ExclusionPredicate = Callable[[CodeRegion], bool]
FunctionListByLine = dict[int, list[FunctionCoverage]]


def function_exclude_not_supported(
    filename: str | None = None,
    lineno: int | None = None,
    columnno: int | None = None,
) -> None:
    """Warn that a function exclude isn't supported."""
    if filename is None:
        LOGGER.warning("Function exclusion not supported for this compiler.")
    else:
        LOGGER.warning(
            "Function exclude marker found on line %s:%s but not supported for this compiler, when processing %s.",
            lineno,
            columnno,
            filename,
        )


def function_exclude_not_at_function_line(
    filename: str, lineno: int, columnno: int
) -> None:
    """Warn that a function exclude is found at a line where no function is defined."""
    LOGGER.warning(
        "Function exclude marker found on line %s:%s but no function definition found, when processing %s.",
        lineno,
        columnno,
        filename,
    )


def get_functions_by_line(filecov: FileCoverage) -> FunctionListByLine:
    """Get dict with the linenumber as key and the function defined in the line as value."""
    functions_by_line: FunctionListByLine = {}
    if filecov is not None:
        for functioncov in filecov.functioncov():
            for lineno in functioncov.pos:
                if lineno not in functions_by_line:
                    functions_by_line[lineno] = []
                functions_by_line[lineno].append(functioncov)

    return functions_by_line


def get_function_exclude_ranges(
    filename: str, lineno: int, columnno: int, *, functions_by_line: FunctionListByLine
) -> list[CodeRegion]:
    """Get the exclude range for a given function."""
    exclude_ranges = list[CodeRegion]()
    if functions_by_line:
        # Find the closest function definition in this line. Check end column if end line is on same line
        function_iter = iter(functions_by_line.get(lineno, []))
        for function in function_iter:
            if (
                lineno in function.pos
                and columnno > function.pos[lineno].column_start
                and (
                    lineno < function.pos[lineno].line_end
                    or columnno < function.pos[lineno].column_end
                )
            ):
                # Now we need to check for nested functions which are included
                included_ranges = [
                    (lineno, function.pos[lineno].line_end + 1)
                    for function in function_iter
                    if function.pos is not None
                ]

                for function_lineno in range(lineno + 1, function.pos[lineno].line_end):
                    included_ranges.extend(
                        (
                            function.pos[function_lineno].line_start,
                            function.pos[function_lineno].line_end,
                        )
                        for function in functions_by_line.get(function_lineno, [])
                    )
                if included_ranges:
                    last_include_end = lineno
                    for include_start, include_end in included_ranges:
                        # The exclusion end must be in the line before
                        exclude_ranges.append(
                            CodeRegion.from_line_range(
                                last_include_end, include_start - 1
                            )
                        )
                        # The next exclusion must start after the included line
                        last_include_end = include_end + 1
                    exclude_ranges.append(
                        CodeRegion.from_line_range(
                            last_include_end, function.pos[lineno].line_end
                        )
                    )
                else:
                    exclude_ranges.append(
                        CodeRegion.from_line_range(
                            lineno, function.pos[lineno].line_end
                        )
                    )
                break
        else:
            function_exclude_not_at_function_line(filename, lineno, columnno)
    else:
        function_exclude_not_supported(filename, lineno, columnno)

    return exclude_ranges


def apply_exclusion_ranges(
    filecov: FileCoverage,
    *,
    line_is_excluded: ExclusionPredicate,
    branch_is_excluded: ExclusionPredicate,
    warn_excluded_lines_with_hits: bool,
) -> None:
    """
    Remove any coverage information that is excluded by explicit markers such as `GCOVR_EXCL_LINE`.

    Modifies the input FileCoverage in place.

    Arguments:
        filecov: The coverage to filter.
        line_is_excluded: The function to check if a line is excluded.
        branch_is_excluded: The function to check if the branches are excluded.
        warn_excluded_lines_with_hits: Warn about excluding lines with hits.

    """
    for linecov_collection in filecov.lines():
        if line_is_excluded(CodeRegion.from_lineno(linecov_collection.lineno)):
            if warn_excluded_lines_with_hits and linecov_collection.count:
                LOGGER.warning(
                    "%s: Line with %d hit(s) excluded.",
                    linecov_collection.location,
                    linecov_collection.count,
                )
            linecov_collection.exclude()

        elif branch_is_excluded(CodeRegion.from_lineno(linecov_collection.lineno)):
            linecov_collection.exclude_branches()

    for functioncov in filecov.functioncov():
        for lineno in functioncov.reportable_linenos:
            if line_is_excluded(CodeRegion.from_lineno(lineno)):
                functioncov.exclude(lineno)


def make_is_in_any_range_inclusive(
    regions: list[CodeRegion],
) -> ExclusionPredicate:
    """
    Create a function to check whether an input is in any range (inclusive).

    This function should provide reasonable performance
    if queries are mostly made in ascending order.

    Examples:
    >>> select = make_is_in_any_range_inclusive([CodeRegion.from_lineno(3), CodeRegion.from_line_range(5, 7)])
    >>> select(CodeRegion.from_lineno(0))
    False
    >>> select(CodeRegion.from_lineno(6))
    True
    >>> [x for x in range(10) if select(CodeRegion.from_lineno(x))]
    [3, 5, 6, 7]

    """
    # values are likely queried in ascending order,
    # allowing the search to start with the first possible range
    regions = sorted(regions)
    hint_region = CodeRegion.from_lineno(0)
    hint_index = 0

    def is_in_any_range(check_region: CodeRegion) -> bool:
        nonlocal hint_region, hint_index

        # if the heuristic failed, restart search from the beginning
        if check_region < hint_region:
            hint_index = 0
        # Remember the current region
        hint_region = check_region

        for current_index in range(hint_index, len(regions)):
            current_region = regions[current_index]
            hint_index = current_index

            # stop as soon as a too-large start is seen
            if check_region.line_start < current_region.line_start:
                break

            if check_region in current_region:
                return True
        else:
            hint_index = len(regions)

        return False

    return is_in_any_range


def _lines_from_sparse(sparse: Iterable[tuple[int, str]]) -> list[str]:
    """
    Convert lineno-source tuples to a flat list, useful for tests.

    >>> _lines_from_sparse([(3, 'foo'), (2, 'bar'), (3, 'foo2')])
    ['', 'bar', 'foo2']
    """
    lines = list[str]()
    for lineno, source in sparse:
        lines.extend("" for _ in range(len(lines), lineno))
        lines[lineno - 1] = source
    return lines
