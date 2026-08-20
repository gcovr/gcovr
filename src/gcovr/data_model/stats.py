# -*- coding:utf-8 -*-

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

from __future__ import annotations
from typing import TypeVar
from dataclasses import dataclass

from ..options import Options


_T = TypeVar("_T")


@dataclass
class SummarizedStats:
    """Data class for the summarized coverage statistics."""

    line: CoverageStat
    branch: CoverageStat
    condition: CoverageStat
    decision: DecisionCoverageStat
    function: CoverageStat
    call: CoverageStat

    @staticmethod
    def new_empty() -> SummarizedStats:
        """Create a empty coverage statistic."""
        return SummarizedStats(
            line=CoverageStat.new_empty(),
            branch=CoverageStat.new_empty(),
            condition=CoverageStat.new_empty(),
            decision=DecisionCoverageStat.new_empty(),
            function=CoverageStat.new_empty(),
            call=CoverageStat.new_empty(),
        )

    def __iadd__(self, other: SummarizedStats) -> SummarizedStats:
        self.line += other.line
        self.branch += other.branch
        self.condition += other.condition
        self.decision += other.decision
        self.function += other.function
        self.call += other.call
        return self

    def serialize(
        self, default_percent: _T, options: Options
    ) -> dict[str, int | float | _T]:
        """Serialize the object."""
        data_dict = dict[str, int | float | _T](
            {
                "line_total": self.line.total,
                "line_covered": self.line.covered,
                "line_percent": self.line.percent_or(default_percent),
                "function_total": self.function.total,
                "function_covered": self.function.covered,
                "function_percent": self.function.percent_or(default_percent),
                "branch_total": self.branch.total,
                "branch_covered": self.branch.covered,
                "branch_percent": self.branch.percent_or(default_percent),
            }
        )
        if self.condition.total != 0:
            data_dict.update(
                {
                    "condition_total": self.condition.total,
                    "condition_covered": self.condition.covered,
                    "condition_percent": self.condition.percent_or(default_percent),
                }
            )

        if options.show_decision:
            data_dict.update(
                {
                    "decision_total": self.decision.total,
                    "decision_covered": self.decision.covered,
                    "decision_percent": self.decision.percent_or(default_percent),
                }
            )

        return data_dict


@dataclass
class CoverageStat:
    """A single coverage metric, e.g. the line coverage percentage of a file."""

    total: int
    """How many elements there were in total."""

    covered: int
    """How many elements were covered."""

    excluded: int
    """How many elements there were excluded."""

    @staticmethod
    def new_empty() -> CoverageStat:
        """Create a empty coverage statistic."""
        return CoverageStat(total=0, covered=0, excluded=0)

    @property
    def percent(self) -> float | None:
        """Percentage of covered elements, equivalent to ``self.percent_or(None)``"""
        return self.percent_or(None)

    def percent_or(self, default: _T) -> float | _T:
        """Percentage of covered elements.

        Coverage is truncated to one decimal:
        >>> CoverageStat(total=10000, covered=1234, excluded=0).percent_or("default")
        12.3

        Coverage is capped at 99.9% unless everything is covered:
        >>> CoverageStat(total=10000, covered=9999, excluded=0).percent_or("default")
        99.9
        >>> CoverageStat(total=10000, covered=10000, excluded=0).percent_or("default")
        100.0

        If there are no elements, percentage is NaN and the default will be returned:
        >>> CoverageStat(total=0, covered=0, excluded=0).percent_or("default")
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
        self.total += other.total
        self.covered += other.covered
        self.excluded += other.excluded
        return self


@dataclass
class DecisionCoverageStat:
    """A CoverageStat for decision coverage (accounts for Uncheckable cases)."""

    total: int
    """How many elements there were in total."""

    covered: int
    """How many elements were covered."""

    uncheckable: int
    """How many elements were uncheckable."""

    @classmethod
    def new_empty(cls) -> DecisionCoverageStat:
        """Create a empty decision coverage statistic."""
        return cls(0, 0, 0)

    @property
    def to_coverage_stat(self) -> CoverageStat:
        """Convert a decision coverage statistic to a coverage statistic."""
        return CoverageStat(total=self.total, covered=self.covered, excluded=0)

    @property
    def percent(self) -> float | None:
        """Return the percent value of the coverage."""
        return self.to_coverage_stat.percent

    def percent_or(self, default: _T) -> float | _T:
        """Return the percent value of the coverage or the given default if no coverage is present."""
        return self.to_coverage_stat.percent_or(default)

    def __iadd__(self, other: DecisionCoverageStat) -> DecisionCoverageStat:
        self.covered += other.covered
        self.total += other.total
        self.uncheckable += other.uncheckable
        return self
