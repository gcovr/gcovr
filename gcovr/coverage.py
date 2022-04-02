# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.1, a parsing and reporting tool for gcov.
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
The gcovr coverage data model.

This module represents the core data structures
and should not have dependencies on any other gcovr module,
also not on the gcovr.utils module.

The data model should contain the exact same information
as the JSON input/output format.
"""

from __future__ import annotations
from typing import Dict, Iterable, Optional, Tuple, TypeVar, Union

_T = TypeVar("_T")


class BranchCoverage:
    r"""Represent coverage information about a branch.

    Args:
        count (int):
            Number of times this branch was followed.
        fallthrough (bool, optional):
            Whether this is a fallthrough branch. None if unknown.
        throw (bool, optional):
            Whether this is an exception-handling branch. None if unknown.
    """

    __slots__ = "count", "fallthrough", "throw"

    def __init__(
        self,
        count: int,
        fallthrough: Optional[bool] = None,
        throw: Optional[bool] = None,
    ) -> None:
        assert count >= 0

        self.count = count
        self.fallthrough = fallthrough
        self.throw = throw

    @property
    def is_covered(self) -> bool:
        return self.count > 0

    def update(self, other: BranchCoverage) -> None:
        r"""Merge BranchCoverage information"""
        self.count += other.count
        if other.fallthrough is not None:
            self.fallthrough = other.fallthrough
        if other.throw is not None:
            self.throw = other.throw


class DecisionCoverageUncheckable:
    r"""Represent coverage information about a decision."""

    def __init__(self) -> None:
        pass

    @property
    def is_uncheckable(self) -> bool:
        return True

    @property
    def is_conditional(self) -> bool:
        return False

    @property
    def is_switch(self) -> bool:
        return False

    def update(self, other: DecisionCoverageUncheckable) -> None:
        r"""Merge DecisionCoverage information"""
        pass


class DecisionCoverageConditional:
    r"""Represent coverage information about a decision.

    Args:
        count_true (int):
            Number of times this decision was made.

        count_false (int):
            Number of times this decision was made.

    """

    __slots__ = "count_true", "count_false"

    def __init__(self, count_true: int, count_false: int) -> None:
        assert count_true >= 0
        self.count_true = count_true
        assert count_false >= 0
        self.count_false = count_false

    @property
    def is_uncheckable(self) -> bool:
        return False

    @property
    def is_conditional(self) -> bool:
        return True

    @property
    def is_switch(self) -> bool:
        return False

    def update(self, other: DecisionCoverageConditional) -> None:
        r"""Merge DecisionCoverage information"""
        self.count_true += other.count_true
        self.count_false += other.count_false


class DecisionCoverageSwitch:
    r"""Represent coverage information about a decision.

    Args:
        count (int):
            Number of times this decision was made.
    """

    __slots__ = "count"

    def __init__(self, count: int) -> None:
        assert count >= 0
        self.count = count

    @property
    def is_uncheckable(self) -> bool:
        return False

    @property
    def is_conditional(self) -> bool:
        return False

    @property
    def is_switch(self) -> bool:
        return True

    def update(self, other: DecisionCoverageSwitch) -> None:
        r"""Merge DecisionCoverage information"""
        self.count += other.count


DecisionCoverage = Union[
    DecisionCoverageUncheckable,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
]


class FunctionCoverage:
    __slots__ = "lineno", "count", "name"

    def __init__(self, name: str, call_count: int = 0) -> None:
        assert call_count >= 0
        self.count = call_count
        self.lineno = 0
        self.name = name

    def update(self, other: FunctionCoverage) -> None:
        r"""Merge FunctionCoverage information"""
        self.count += other.count
        if self.lineno == 0:
            self.lineno = other.lineno
        else:
            assert self.lineno == other.lineno


class LineCoverage:
    r"""Represent coverage information about a line.

    Args:
        lineno (int):
            The line number.
        count (int):
            How often this line was executed at least partially.
        noncode (bool, optional):
            Whether any coverage info on this line should be ignored.
        excluded (bool, optional):
            Whether this line is excluded by a marker.
    """

    __slots__ = (
        "lineno",
        "count",
        "noncode",
        "excluded",
        "branches",
        "decision",
        "functions",
    )

    def __init__(
        self, lineno: int, count: int = 0, noncode: bool = False, excluded: bool = False
    ) -> None:
        assert lineno > 0
        assert count >= 0

        self.lineno: int = lineno
        self.count: int = count
        self.noncode: bool = noncode
        self.excluded: bool = excluded
        self.branches: Dict[int, BranchCoverage] = {}
        self.decision: Optional[DecisionCoverage] = None

    @property
    def is_excluded(self) -> bool:
        return self.excluded

    @property
    def is_covered(self) -> bool:
        if self.noncode:
            return False
        return self.count > 0

    @property
    def is_uncovered(self) -> bool:
        if self.noncode:
            return False
        return self.count == 0

    def branch(self, branch_id: int) -> BranchCoverage:
        r"""Get or create the BranchCoverage for that branch_id."""
        try:
            return self.branches[branch_id]
        except KeyError:
            self.branches[branch_id] = branch_cov = BranchCoverage(0)
            return branch_cov

    def update(self, other: LineCoverage) -> None:
        r"""Merge LineCoverage information."""
        assert self.lineno == other.lineno
        self.count += other.count
        self.noncode &= other.noncode
        self.excluded |= other.excluded

        for branch_id, branch_cov in other.branches.items():
            self.branch(branch_id).update(branch_cov)

        if self.decision is None:
            self.decision = other.decision
        else:
            self.decision.update(other.decision)

    def branch_coverage(self) -> Tuple[int, int, Optional[float]]:
        total = len(self.branches)
        cover = 0
        for branch in self.branches.values():
            if branch.is_covered:
                cover += 1

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, percent

    def decision_coverage(self) -> Tuple[int, int, int, Optional[float]]:
        total = 0
        cover = 0
        unchecked = False
        if self.decision is not None:
            if self.decision.is_uncheckable:
                total = 2
                unchecked = True
            elif self.decision.is_conditional:
                total = 2
                if self.decision.count_true > 0:
                    cover += 1
                if self.decision.count_false > 0:
                    cover += 1
            elif self.decision.is_switch:
                total = 1
                if self.decision.count > 0:
                    cover += 1
            else:
                RuntimeError("Unknown decision type")

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, unchecked, percent


class FileCoverage:
    __slots__ = "filename", "functions", "lines"

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.functions: Dict[str, FunctionCoverage] = {}
        self.lines: Dict[int, LineCoverage] = {}

    def line(self, lineno: int, **defaults) -> LineCoverage:
        r"""Get or create the LineCoverage for that lineno."""
        try:
            return self.lines[lineno]
        except KeyError:
            self.lines[lineno] = line_cov = LineCoverage(lineno, **defaults)
            return line_cov

    def function(self, function_name: str) -> FunctionCoverage:
        r"""Get or create the FunctionCoverage for that function."""
        try:
            return self.functions[function_name]
        except KeyError:
            self.functions[function_name] = function_cov = FunctionCoverage(
                function_name
            )
            return function_cov

    def update(self, other: FileCoverage) -> None:
        r"""Merge FileCoverage information."""
        assert self.filename == other.filename
        for lineno, line_cov in other.lines.items():
            self.line(lineno, noncode=True, excluded=False).update(line_cov)
        for fct_name, fct_cov in other.functions.items():
            self.function(fct_name).update(fct_cov)

    def uncovered_lines_str(self) -> str:
        uncovered_lines = sorted(
            lineno for lineno, line in self.lines.items() if line.is_uncovered
        )

        if not uncovered_lines:
            return ""

        # Walk through the uncovered lines in sorted order.
        # Find blocks of consecutive uncovered lines, and return
        # a string with that information.
        #
        # Should we include noncode lines in the range of lines
        # to be covered???  This simplifies the ranges summary, but it
        # provides a counterintuitive listing.
        return ",".join(
            _format_range(first, last)
            for first, last in _find_consecutive_ranges(uncovered_lines)
        )

    def uncovered_branches_str(self) -> str:
        uncovered_lines = sorted(
            lineno
            for lineno, line in self.lines.items()
            if not all(branch.is_covered for branch in line.branches.values())
        )

        # Don't do any aggregation on branch results
        return ",".join(str(x) for x in uncovered_lines)

    def function_coverage(self) -> Tuple[int, int, Optional[float]]:
        total = len(self.functions.values())
        cover = 0
        for function in self.functions.values():
            cover += 1 if function.count > 0 else 0

        percent = calculate_coverage(cover, total, nan_value=None)

        return total, cover, percent

    def line_coverage(self) -> Tuple[int, int, Optional[float]]:
        total = 0
        cover = 0
        for line in self.lines.values():
            if line.is_covered or line.is_uncovered:
                total += 1
            if line.is_covered:
                cover += 1

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, percent

    def branch_coverage(self) -> Tuple[int, int, Optional[float]]:
        total = 0
        cover = 0
        for line in self.lines.values():
            b_total, b_cover, _ = line.branch_coverage()
            total += b_total
            cover += b_cover

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, percent

    def decision_coverage(self) -> Tuple[int, int, int, Optional[float]]:
        total = 0
        cover = 0
        unchecked = 0
        for line in self.lines.values():
            d_total, d_cover, d_unchecked, _ = line.decision_coverage()
            total += d_total
            cover += d_cover
            unchecked += d_unchecked

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, unchecked, percent


CovData = Dict[str, FileCoverage]


def _find_consecutive_ranges(items: Iterable[int]) -> Iterable[Tuple[int, int]]:
    first = last = None
    for item in items:
        if last is None:
            first = last = item
            continue

        if item == (last + 1):
            last = item
            continue

        assert first is not None
        yield first, last
        first = last = item

    if last is not None:
        assert first is not None
        yield first, last


def _format_range(first: int, last: int) -> str:
    if first == last:
        return str(first)
    return "{first}-{last}".format(first=first, last=last)


def get_global_stats(covdata: CovData):
    """Get global statistics"""
    lines_total = 0
    lines_covered = 0
    functions_total = 0
    functions_covered = 0
    branches_total = 0
    branches_covered = 0

    keys = list(covdata.keys())

    for key in keys:
        (total, covered, _) = covdata[key].line_coverage()
        lines_total += total
        lines_covered += covered

        (total, covered, _) = covdata[key].function_coverage()
        functions_total += total
        functions_covered += covered

        (total, covered, _) = covdata[key].branch_coverage()
        branches_total += total
        branches_covered += covered

    percent = calculate_coverage(lines_covered, lines_total)
    percent_functions = calculate_coverage(functions_covered, functions_total)
    percent_branches = calculate_coverage(branches_covered, branches_total)

    return (
        lines_total,
        lines_covered,
        percent,
        functions_total,
        functions_covered,
        percent_functions,
        branches_total,
        branches_covered,
        percent_branches,
    )


def calculate_coverage(
    covered: int,
    total: int,
    nan_value: _T = 0.0,
) -> Union[float, _T]:
    coverage = nan_value
    if total != 0:
        coverage = round(100.0 * covered / total, 1)
        # If we get 100.0% and not all branches are covered use 99.9%
        if (coverage == 100.0) and (covered != total):
            coverage = 99.9

    return coverage
