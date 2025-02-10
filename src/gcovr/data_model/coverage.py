# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
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
import logging
from typing import Optional, Union

from .stats import CoverageStat, DecisionCoverageStat, SummarizedStats

LOGGER = logging.getLogger("gcovr")


class BranchCoverage:
    r"""Represent coverage information about a branch.

    Args:
        source_block_id (int):
            The block number.
        count (int):
            Number of times this branch was followed.
        fallthrough (bool, optional):
            Whether this is a fallthrough branch. False if unknown.
        throw (bool, optional):
            Whether this is an exception-handling branch. False if unknown.
        destination_block_id (int, optional):
            The destination block of the branch. None if unknown.
        excluded (bool, optional):
            Whether the branch is excluded.
    """

    first_undefined_source_block_id: bool = True

    __slots__ = (
        "source_block_id",
        "count",
        "fallthrough",
        "throw",
        "destination_block_id",
        "excluded",
    )

    def __init__(
        self,
        source_block_id: Optional[int],
        count: int,
        fallthrough: bool = False,
        throw: bool = False,
        destination_block_id: Optional[int] = None,
        excluded: Optional[bool] = None,
    ) -> None:
        if count < 0:
            raise AssertionError("count must not be a negative value.")

        self.source_block_id = source_block_id
        self.count = count
        self.fallthrough = fallthrough
        self.throw = throw
        self.destination_block_id = destination_block_id
        self.excluded = excluded

    @property
    def source_block_id_or_0(self) -> int:
        """Get a valid block number (0) if there was no definition in GCOV file."""
        if self.source_block_id is None:
            self.source_block_id = 0
            if BranchCoverage.first_undefined_source_block_id:
                BranchCoverage.first_undefined_source_block_id = False
                LOGGER.info("No block number defined, assuming 0 for all undefined")

        return self.source_block_id

    @property
    def is_excluded(self) -> bool:
        """Return True if the branch is excluded."""
        return False if self.excluded is None else self.excluded

    @property
    def is_reportable(self) -> bool:
        """Return True if the branch is reportable."""
        return not self.excluded

    @property
    def is_covered(self) -> bool:
        """Return True if the branch is covered."""
        return self.is_reportable and self.count > 0


class CallCoverage:
    r"""Represent coverage information about a call.

    Args:
        callno (int):
            The number of the call.
        covered (bool):
            Whether the call was performed.
        excluded (bool, optional):
            Whether the call is excluded.
    """

    __slots__ = "callno", "covered", "excluded"

    def __init__(
        self,
        callno: int,
        covered: bool,
        excluded: Optional[bool] = False,
    ) -> None:
        self.callno = callno
        self.covered = covered
        self.excluded = excluded

    @property
    def is_reportable(self) -> bool:
        """Return True if the call is reportable."""
        return not self.excluded

    @property
    def is_covered(self) -> bool:
        """Return True if the call is covered."""
        return self.is_reportable and self.covered


class ConditionCoverage:
    r"""Represent coverage information about a condition.

    Args:
        count (int):
            The number of the call.
        covered (int):
            Whether the call was performed.
        not_covered_true list[int]:
            The conditions which were not true.
        not_covered_false list[int]:
            The conditions which were not false.
        excluded (bool, optional):
            Whether the condition is excluded.
    """

    __slots__ = "count", "covered", "not_covered_true", "not_covered_false", "excluded"

    def __init__(
        self,
        count: int,
        covered: int,
        not_covered_true: list[int],
        not_covered_false: list[int],
        excluded: Optional[bool] = False,
    ) -> None:
        if count < 0:
            raise AssertionError("count must not be a negative value.")
        if count < covered:
            raise AssertionError("count must not be less than covered.")
        self.count = count
        self.covered = covered
        self.not_covered_true = not_covered_true
        self.not_covered_false = not_covered_false
        self.excluded = excluded


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
        if count_true < 0:
            raise AssertionError("count_true must not be a negative value.")
        self.count_true = count_true
        if count_false < 0:
            raise AssertionError("count_true must not be a negative value.")
        self.count_false = count_false


class DecisionCoverageSwitch:
    r"""Represent coverage information about a decision.

    Args:
        count (int):
            Number of times this decision was made.
    """

    __slots__ = ("count",)

    def __init__(self, count: int) -> None:
        if count < 0:
            raise AssertionError("count must not be a negative value.")
        self.count = count


DecisionCoverage = Union[
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
]


class FunctionCoverage:
    r"""Represent coverage information about a function.

    The counter is stored as dictionary with the line as key to be able
    to merge function coverage in different ways

    Args:
        name (str):
            The mangled name of the function, None if not available.
        demangled_name (str):
            The demangled name (signature) of the functions.
        lineno (int):
            The line number.
        count (int):
            How often this function was executed.
        blocks (float):
            Block coverage of function.
        start ((int, int)), optional):
            Tuple with function start line and column.
        end ((int, int)), optional):
            Tuple with function end line and column.
        excluded (bool, optional):
            Whether this line is excluded by a marker.
    """

    __slots__ = (
        "name",
        "demangled_name",
        "count",
        "blocks",
        "start",
        "end",
        "excluded",
    )

    def __init__(
        self,
        name: Optional[str],
        demangled_name: str,
        *,
        lineno: int,
        count: int,
        blocks: float,
        start: Optional[tuple[int, int]] = None,
        end: Optional[tuple[int, int]] = None,
        excluded: bool = False,
    ) -> None:
        if count < 0:
            raise AssertionError("count must not be a negative value.")
        self.name = name
        self.demangled_name = demangled_name
        self.count = dict[int, int]({lineno: count})
        self.blocks = dict[int, float]({lineno: blocks})
        self.excluded = dict[int, bool]({lineno: excluded})
        self.start: Optional[dict[int, tuple[int, int]]] = (
            None if start is None else {lineno: start}
        )
        self.end: Optional[dict[int, tuple[int, int]]] = (
            None if end is None else {lineno: end}
        )


class LineCoverage:
    r"""Represent coverage information about a line.

    Each line is either *excluded* or *reportable*.

    A *reportable* line is either *covered* or *uncovered*.

    The default state of a line is *coverable*/*reportable*/*uncovered*.

    Args:
        lineno (int):
            The line number.
        count (int):
            How often this line was executed at least partially.
        function_name (str, optional):
            Mangled name of the function the line belongs to.
        block_ids (*int, optional):
            List of block ids in this line
        excluded (bool, optional):
            Whether this line is excluded by a marker.
        md5 (str, optional):
            The md5 checksum of the source code line.
    """

    __slots__ = (
        "lineno",
        "count",
        "function_name",
        "block_ids",
        "excluded",
        "md5",
        "branches",
        "conditions",
        "decision",
        "calls",
    )

    def __init__(
        self,
        lineno: int,
        count: int,
        function_name: Optional[str] = None,
        block_ids: Optional[list[int]] = None,
        md5: Optional[str] = None,
        excluded: bool = False,
    ) -> None:
        if lineno <= 0:
            raise AssertionError("Line number must be a positive value.")
        if count < 0:
            raise AssertionError("count must not be a negative value.")

        self.lineno: int = lineno
        self.count: int = count
        self.function_name: Optional[str] = function_name
        self.block_ids: Optional[list[int]] = block_ids
        self.md5: Optional[str] = md5
        self.excluded: bool = excluded
        self.branches = dict[int, BranchCoverage]()
        self.conditions = dict[int, ConditionCoverage]()
        self.decision: Optional[DecisionCoverage] = None
        self.calls = dict[int, CallCoverage]()

    @property
    def is_excluded(self) -> bool:
        """Return True if the line is excluded."""
        return self.excluded

    @property
    def is_reportable(self) -> bool:
        """Return True if the line is reportable."""
        return not self.excluded

    @property
    def is_covered(self) -> bool:
        """Return True if the line is covered."""
        return self.is_reportable and self.count > 0

    @property
    def is_uncovered(self) -> bool:
        """Return True if the line is uncovered."""
        return self.is_reportable and self.count == 0

    @property
    def has_uncovered_branch(self) -> bool:
        """Return True if the line has a uncovered branches."""
        return not all(
            branchcov.is_covered or branchcov.is_excluded
            for branchcov in self.branches.values()
        )

    @property
    def has_uncovered_decision(self) -> bool:
        """Return True if the line has a uncovered decision."""
        if self.decision is None:
            return False

        if isinstance(self.decision, DecisionCoverageUncheckable):
            return False

        if isinstance(self.decision, DecisionCoverageConditional):
            return self.decision.count_true == 0 or self.decision.count_false == 0

        if isinstance(self.decision, DecisionCoverageSwitch):
            return self.decision.count == 0

        raise AssertionError(f"Unknown decision type: {self.decision!r}")

    def exclude(self) -> None:
        """Exclude line from coverage statistic."""
        self.excluded = True
        self.count = 0
        self.branches.clear()
        self.conditions.clear()
        self.decision = None
        self.calls.clear()

    def branch_coverage(self) -> CoverageStat:
        """Return the branch coverage statistic of the line."""
        total = 0
        covered = 0
        for branchcov in self.branches.values():
            if branchcov.is_reportable:
                total += 1
                if branchcov.is_covered:
                    covered += 1
        return CoverageStat(covered=covered, total=total)

    def condition_coverage(self) -> CoverageStat:
        """Return the condition coverage statistic of the line."""
        total = 0
        covered = 0
        for condition in self.conditions.values():
            total += condition.count
            covered += condition.covered
        return CoverageStat(covered=covered, total=total)

    def decision_coverage(self) -> DecisionCoverageStat:
        """Return the decision coverage statistic of the line."""
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

        raise AssertionError(f"Unknown decision type: {self.decision!r}")


class FileCoverage:
    """Represent coverage information about a file."""

    __slots__ = "filename", "functions", "lines", "data_sources"

    def __init__(
        self, filename: str, data_source: Optional[Union[str, set[str]]]
    ) -> None:
        self.filename: str = filename
        self.functions = dict[str, FunctionCoverage]()
        self.lines = dict[int, LineCoverage]()
        self.data_sources = (
            set[str]()
            if data_source is None
            else set[str](
                [data_source] if isinstance(data_source, str) else data_source
            )
        )

    def filter_for_function(self, functioncov: FunctionCoverage) -> FileCoverage:
        """Get a file coverage object reduced to a single function"""
        if functioncov.name not in self.functions:
            raise AssertionError(
                f"Function {functioncov.name} must be in filtered file coverage object."
            )
        if functioncov.name is None:
            raise AssertionError(
                "Data for filtering is missing. Need supported GCOV JSON format to get the information."
            )
        filecov = FileCoverage(self.filename, self.data_sources)
        filecov.functions[functioncov.name] = functioncov

        filecov.lines = {
            lineno: linecov
            for lineno, linecov in self.lines.items()
            if linecov.function_name == functioncov.name
        }

        return filecov

    @property
    def stats(self) -> SummarizedStats:
        """Create a coverage statistic of a file coverage object."""
        return SummarizedStats(
            line=self.line_coverage(),
            branch=self.branch_coverage(),
            condition=self.condition_coverage(),
            decision=self.decision_coverage(),
            function=self.function_coverage(),
            call=self.call_coverage(),
        )

    def function_coverage(self) -> CoverageStat:
        """Return the function coverage statistic of the file."""
        total = 0
        covered = 0

        for functioncov in self.functions.values():
            for lineno, excluded in functioncov.excluded.items():
                if not excluded:
                    total += 1
                    if functioncov.count[lineno] > 0:
                        covered += 1

        return CoverageStat(covered, total)

    def line_coverage(self) -> CoverageStat:
        """Return the line coverage statistic of the file."""
        total = 0
        covered = 0

        for linecov in self.lines.values():
            if linecov.is_reportable:
                total += 1
                if linecov.is_covered:
                    covered += 1

        return CoverageStat(covered, total)

    def branch_coverage(self) -> CoverageStat:
        """Return the branch coverage statistic of the file."""
        stat = CoverageStat.new_empty()

        for linecov in self.lines.values():
            if linecov.is_reportable:
                stat += linecov.branch_coverage()

        return stat

    def condition_coverage(self) -> CoverageStat:
        """Return the condition coverage statistic of the file."""
        stat = CoverageStat.new_empty()

        for linecov in self.lines.values():
            if linecov.is_reportable:
                stat += linecov.condition_coverage()

        return stat

    def decision_coverage(self) -> DecisionCoverageStat:
        """Return the decision coverage statistic of the file."""
        stat = DecisionCoverageStat.new_empty()

        for linecov in self.lines.values():
            if linecov.is_reportable:
                stat += linecov.decision_coverage()

        return stat

    def call_coverage(self) -> CoverageStat:
        """Return the call coverage statistic of the file."""
        covered = 0
        total = 0

        for linecov in self.lines.values():
            if linecov.is_reportable and len(linecov.calls) > 0:
                for callcov in linecov.calls.values():
                    if callcov.is_reportable:
                        total += 1
                        if callcov.is_covered:
                            covered += 1

        return CoverageStat(covered, total)
