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
The gcovr coverage data model.

This module represents the core data structures
and should not have dependencies on any other gcovr module,
also not on the gcovr.utils module.

The data model should contain the exact same information
as the JSON input/output format.

The types ending with ``*Coverage``
contain per-project/-line/-decision/-branch coverage.

The types ``SummarizedStats``, ``CoverageStat``, and ``DecisionCoverageStat``
report aggregated metrics/percentages.
"""

from __future__ import annotations
from typing import Dict, Optional, TypeVar, Union
from dataclasses import dataclass

_T = TypeVar("_T")


class BranchCoverage:
    r"""Represent coverage information about a branch.

    Args:
        count (int):
            Number of times this branch was followed.
        fallthrough (bool, optional):
            Whether this is a fallthrough branch. False if unknown.
        throw (bool, optional):
            Whether this is an exception-handling branch. False if unknown.
    """

    __slots__ = "count", "fallthrough", "throw"

    def __init__(
        self,
        count: int,
        fallthrough: bool = False,
        throw: bool = False,
    ) -> None:
        assert count >= 0

        self.count = count
        self.fallthrough = fallthrough
        self.throw = throw

    @property
    def is_covered(self) -> bool:
        return self.count > 0


class DecisionCoverageUncheckable:
    r"""Represent coverage information about a decision."""

    __slots__ = ()

    def __init__(self) -> None:
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


class DecisionCoverageSwitch:
    r"""Represent coverage information about a decision.

    Args:
        count (int):
            Number of times this decision was made.
    """

    __slots__ = ("count",)

    def __init__(self, count: int) -> None:
        assert count >= 0
        self.count = count


DecisionCoverage = Union[
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
]


class FunctionCoverage:
    __slots__ = "lineno", "count", "name"

    def __init__(self, name: str, *, lineno: int = 0, call_count: int = 0) -> None:
        assert call_count >= 0
        self.count = call_count
        self.lineno = lineno
        self.name = name


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

    @property
    def has_uncovered_branch(self) -> bool:
        return not all(branch.is_covered for branch in self.branches.values())

    def branch_coverage(self) -> CoverageStat:
        total = len(self.branches)
        covered = 0
        for branch in self.branches.values():
            if branch.is_covered:
                covered += 1

        return CoverageStat(covered=covered, total=total)

    def decision_coverage(self) -> DecisionCoverageStat:
        if self.decision is None:
            return DecisionCoverageStat(0, 0, 0)

        if isinstance(self.decision, DecisionCoverageUncheckable):
            return DecisionCoverageStat(0, 1, 2)  # TODO should it be uncheckable=2?

        if isinstance(self.decision, DecisionCoverageConditional):
            covered = 0
            if self.decision.count_true > 0:
                covered += 1
            if self.decision.count_false > 0:
                covered += 1
            return DecisionCoverageStat(covered, 0, 2)

        if isinstance(self.decision, DecisionCoverageSwitch):
            covered = 0
            if self.decision.count > 0:
                covered += 1
            return DecisionCoverageStat(covered, 0, 1)

        raise RuntimeError(f"Unknown decision type: {self.decision!r}")


class FileCoverage:
    __slots__ = "filename", "functions", "lines"

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.functions: Dict[str, FunctionCoverage] = {}
        self.lines: Dict[int, LineCoverage] = {}

    def function_coverage(self) -> CoverageStat:
        total = len(self.functions.values())
        covered = 0

        for function in self.functions.values():
            if function.count > 0:
                covered += 1

        return CoverageStat(covered, total)

    def line_coverage(self) -> CoverageStat:
        total = 0
        covered = 0

        for line in self.lines.values():
            if line.is_covered or line.is_uncovered:
                total += 1
            if line.is_covered:
                covered += 1

        return CoverageStat(covered, total)

    def branch_coverage(self) -> CoverageStat:
        stat = CoverageStat.new_empty()

        for line in self.lines.values():
            if line.is_covered or line.is_uncovered:
                stat += line.branch_coverage()

        return stat

    def decision_coverage(self) -> DecisionCoverageStat:
        stat = DecisionCoverageStat.new_empty()

        for line in self.lines.values():
            if line.is_covered or line.is_uncovered:
                stat += line.decision_coverage()

        return stat


CovData = Dict[str, FileCoverage]


@dataclass
class SummarizedStats:
    line: CoverageStat
    branch: CoverageStat
    function: CoverageStat
    decision: DecisionCoverageStat

    @staticmethod
    def new_empty() -> SummarizedStats:
        return SummarizedStats(
            line=CoverageStat.new_empty(),
            branch=CoverageStat.new_empty(),
            function=CoverageStat.new_empty(),
            decision=DecisionCoverageStat.new_empty(),
        )

    @staticmethod
    def from_covdata(covdata: CovData) -> SummarizedStats:
        stats = SummarizedStats.new_empty()
        for filecov in covdata.values():
            stats += SummarizedStats.from_file(filecov)
        return stats

    @staticmethod
    def from_file(filecov: FileCoverage) -> SummarizedStats:
        return SummarizedStats(
            line=filecov.line_coverage(),
            branch=filecov.branch_coverage(),
            function=filecov.function_coverage(),
            decision=filecov.decision_coverage(),
        )

    def __iadd__(self, other: SummarizedStats) -> SummarizedStats:
        self.line += other.line
        self.branch += other.branch
        self.function += other.function
        self.decision += other.decision
        return self


@dataclass
class CoverageStat:
    """A single coverage metric, e.g. the line coverage percentage of a file."""

    covered: int
    """How many elements were covered."""

    total: int
    """How many elements there were in total."""

    @staticmethod
    def new_empty() -> CoverageStat:
        return CoverageStat(0, 0)

    @property
    def percent(self) -> Optional[float]:
        """Percentage of covered elements, equivalent to ``self.percent_or(None)``"""
        return self.percent_or(None)

    def percent_or(self, default: _T) -> Union[float, _T]:
        """
        Percentage of covered elements.

        Coverage is truncated to one decimal:
        >>> CoverageStat(1234, 10000).percent_or("default")
        12.3

        Coverage is capped at 99.9% unless everything is covered:
        >>> CoverageStat(9999, 10000).percent_or("default")
        99.9
        >>> CoverageStat(10000, 10000).percent_or("default")
        100.0

        If there are no elements, percentage is NaN and the default will be returned:
        >>> CoverageStat(0, 0).percent_or("default")
        'default'
        """
        if not self.total:
            return default

        # Return 100% only if covered == total.
        if self.covered == self.total:
            return 100.0

        # There is at least one uncovered item.
        # Round to 1 decimal and clamp to max 99.9%.
        ratio = self.covered / self.total
        return min(99.9, round(ratio * 100.0, 1))

    def __iadd__(self, other: CoverageStat) -> CoverageStat:
        self.covered += other.covered
        self.total += other.total
        return self


@dataclass
class DecisionCoverageStat:
    """A CoverageStat for decision coverage (accounts for Uncheckable cases)."""

    covered: int
    uncheckable: int
    total: int

    @classmethod
    def new_empty(cls) -> DecisionCoverageStat:
        return cls(0, 0, 0)

    @property
    def to_coverage_stat(self) -> CoverageStat:
        return CoverageStat(covered=self.covered, total=self.total)

    @property
    def percent(self) -> Optional[float]:
        return self.to_coverage_stat.percent

    def percent_or(self, default: _T) -> Union[float, _T]:
        return self.to_coverage_stat.percent_or(default)

    def __iadd__(self, other: DecisionCoverageStat) -> DecisionCoverageStat:
        self.covered += other.covered
        self.uncheckable += other.uncheckable
        self.total += other.total
        return self
