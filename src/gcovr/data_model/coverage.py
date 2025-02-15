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

from .coverage_dict import CoverageDict
from .merging import DEFAULT_MERGE_OPTIONS, GcovrMergeAssertionError, MergeOptions
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

    def merge(
        self,
        other: BranchCoverage,
        _options: MergeOptions,
        _context: Optional[str],
    ) -> None:
        """
        Merge BranchCoverage information.

        Do not use 'other' objects afterwards!

            Examples:
        >>> left = BranchCoverage(1, 2)
        >>> right = BranchCoverage(1, 3, False, True)
        >>> right.excluded = True
        >>> left.merge(right, DEFAULT_MERGE_OPTIONS, None)
        >>> left.count
        5
        >>> left.fallthrough
        False
        >>> left.throw
        True
        >>> left.excluded
        True
        """

        self.count += other.count
        self.fallthrough |= other.fallthrough
        self.throw |= other.throw
        if self.excluded is True or other.excluded is True:
            self.excluded = True

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

    def merge(
        self,
        other: CallCoverage,
        _options: MergeOptions,
        context: Optional[str],
    ) -> CallCoverage:
        """
        Merge CallCoverage information.

        Do not use 'left' or 'right' objects afterwards!
        """
        if self.callno != other.callno:
            raise AssertionError(
                f"Call number must be equal, got {self.callno} and {other.callno} while merging {context}."
            )
        self.covered |= other.covered
        return self

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

    def merge(
        self,
        other: ConditionCoverage,
        options: MergeOptions,
        context: Optional[str],
    ) -> None:
        """
        Merge ConditionCoverage information.

        Do not use 'other' objects afterwards!

        Examples:
        >>> left = ConditionCoverage(4, 2, [1, 2], [])
        >>> right = ConditionCoverage(4, 3, [2], [1, 3])
        >>> left.merge(None, DEFAULT_MERGE_OPTIONS, None)
        >>> left.count
        4
        >>> left.covered
        2
        >>> left.not_covered_true
        [1, 2]
        >>> left.not_covered_false
        []
        >>> left.merge(right, DEFAULT_MERGE_OPTIONS, None)
        >>> left.count
        4
        >>> left.covered
        3
        >>> left.not_covered_true
        [2]
        >>> left.not_covered_false
        []

        If ``options.cond_opts.merge_condition_fold`` is set,
        the two condition coverage lists can have differing counts.
        The conditions are shrunk to match the lowest count
        """

        if other is not None:
            if self.count != other.count:
                if options.cond_opts.merge_condition_fold:
                    LOGGER.warning(
                        f"Condition counts are not equal, got {other.count} and expected {self.count}. "
                        f"Reducing to {min(self.count, other.count)}."
                    )
                    if self.count > other.count:
                        self.not_covered_true = self.not_covered_true[
                            : len(other.not_covered_true)
                        ]
                        self.not_covered_false = self.not_covered_false[
                            : len(other.not_covered_false)
                        ]
                        self.count = other.count
                    else:
                        other.not_covered_true = other.not_covered_true[
                            : len(self.not_covered_true)
                        ]
                        other.not_covered_false = other.not_covered_false[
                            : len(self.not_covered_false)
                        ]
                        other.count = self.count
                else:
                    raise AssertionError(
                        f"The number of conditions must be equal, got {other.count} and expected {self.count} while merging {context}.\n"
                        "\tYou can run gcovr with --merge-mode-conditions=MERGE_MODE.\n"
                        "\tThe available values for MERGE_MODE are described in the documentation."
                    )

            self.not_covered_false = sorted(
                list(set(self.not_covered_false) & set(other.not_covered_false))
            )
            self.not_covered_true = sorted(
                list(set(self.not_covered_true) & set(other.not_covered_true))
            )
            self.covered = (
                self.count - len(self.not_covered_false) - len(self.not_covered_true)
            )


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
        self.count = CoverageDict[int, int]({lineno: count})
        self.blocks = CoverageDict[int, float]({lineno: blocks})
        self.excluded = CoverageDict[int, bool]({lineno: excluded})
        self.start: Optional[CoverageDict[int, tuple[int, int]]] = (
            None
            if start is None
            else CoverageDict[int, tuple[int, int]]({lineno: start})
        )
        self.end: Optional[CoverageDict[int, tuple[int, int]]] = (
            None if end is None else CoverageDict[int, tuple[int, int]]({lineno: end})
        )

    def merge(
        self,
        other: FunctionCoverage,
        options: MergeOptions,
        context: Optional[str],
    ) -> FunctionCoverage:
        """
        Merge FunctionCoverage information.

        Do not use 'left' or 'right' objects afterwards!

        Precondition: both objects must have same name and lineno.

        If ``options.func_opts.ignore_function_lineno`` is set,
        the two function coverage objects can have differing line numbers.
        With following flags the merge mode can be defined:
        - ``options.func_opts.merge_function_use_line_zero``
        - ``options.func_opts.merge_function_use_line_min``
        - ``options.func_opts.merge_function_use_line_max``
        - ``options.func_opts.separate_function``
        """
        if self.demangled_name != other.demangled_name:
            raise AssertionError("Function demangled name must be equal.")
        if self.name != other.name:
            raise AssertionError("Function name must be equal.")
        if not options.func_opts.ignore_function_lineno:
            if self.count.keys() != other.count.keys():
                lines = sorted(set([*self.count.keys(), *other.count.keys()]))
                raise GcovrMergeAssertionError(
                    f"Got function {other.demangled_name} in {context} on multiple lines: {', '.join([str(line) for line in lines])}.\n"
                    "\tYou can run gcovr with --merge-mode-functions=MERGE_MODE.\n"
                    "\tThe available values for MERGE_MODE are described in the documentation."
                )

        # keep distinct counts for each line number
        if options.func_opts.separate_function:
            for lineno, count in sorted(other.count.items()):
                try:
                    self.count[lineno] += count
                except KeyError:
                    self.count[lineno] = count
            for lineno, blocks in other.blocks.items():
                try:
                    # Take the maximum value for this line
                    if self.blocks[lineno] < blocks:
                        self.blocks[lineno] = blocks
                except KeyError:
                    self.blocks[lineno] = blocks
            for lineno, excluded in other.excluded.items():
                try:
                    self.excluded[lineno] |= excluded
                except KeyError:
                    self.excluded[lineno] = excluded
            if other.start is not None:
                if self.start is None:
                    self.start = CoverageDict[int, tuple[int, int]]()
                for lineno, start in other.start.items():
                    self.start[lineno] = start
            if other.end is not None:
                if self.end is None:
                    self.end = CoverageDict[int, tuple[int, int]]()
                for lineno, end in other.end.items():
                    self.end[lineno] = end
            return self

        right_lineno = list(other.count.keys())[0]
        # merge all counts into an entry for a single line number
        if right_lineno in self.count:
            lineno = right_lineno
        elif options.func_opts.merge_function_use_line_zero:
            lineno = 0
        elif options.func_opts.merge_function_use_line_min:
            lineno = min(*self.count.keys(), *other.count.keys())
        elif options.func_opts.merge_function_use_line_max:
            lineno = max(*self.count.keys(), *other.count.keys())
        else:
            raise AssertionError("Sanity check, unknown merge mode")

        # Overwrite data with the sum at the desired line
        self.count = CoverageDict[int, int](
            {lineno: sum(self.count.values()) + sum(other.count.values())}
        )
        # or the max value at the desired line
        self.blocks = CoverageDict[int, float](
            {lineno: max(*self.blocks.values(), *other.blocks.values())}
        )
        # or the logical or of all values
        self.excluded = CoverageDict[int, bool](
            {lineno: any(self.excluded.values()) or any(other.excluded.values())}
        )

        if self.start is not None and other.start is not None:
            # or the minimum start
            self.start = CoverageDict[int, tuple[int, int]](
                {lineno: min(*self.start.values(), *other.start.values())}
            )
        if self.end is not None and other.end is not None:
            # or the maximum end
            self.end = CoverageDict[int, tuple[int, int]](
                {lineno: max(*self.end.values(), *other.end.values())}
            )

        return self


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
        self.branches = CoverageDict[int, BranchCoverage]()
        self.conditions = CoverageDict[int, ConditionCoverage]()
        self.decision: Optional[DecisionCoverage] = None
        self.calls = CoverageDict[int, CallCoverage]()

    def merge(
        self,
        other: LineCoverage,
        options: MergeOptions,
        context: Optional[str],
    ) -> LineCoverage:
        """
        Merge LineCoverage information.

        Do not use 'left' or 'right' objects afterwards!

        Precondition: both objects must have same lineno.
        """
        context = f"{context}:{self.lineno}"
        if self.lineno != other.lineno:
            raise AssertionError("Line number must be equal.")
        # If both checksums exists compare them if only one exists, use it.
        if self.md5 is not None and other.md5 is not None:
            if self.md5 != other.md5:
                raise AssertionError(f"MD5 checksum of {context} must be equal.")
        elif other.md5 is not None:
            self.md5 = other.md5

        self.count += other.count
        self.excluded |= other.excluded
        self.branches.merge(other.branches, options, context)
        self.conditions.merge(other.conditions, options, context)
        self.__merge_decision(other.decision)
        self.calls.merge(other.calls, options, context)

        return self

    def __merge_decision(  # pylint: disable=too-many-return-statements
        self,
        decisioncov: Optional[DecisionCoverage],
    ) -> None:
        """Merge DecisionCoverage information.

        The DecisionCoverage has different states:

        - None (no known decision)
        - Uncheckable (there was a decision, but it can't be analyzed properly)
        - Conditional
        - Switch

        If there is a conflict between different types, Uncheckable will be returned.
        """

        # The DecisionCoverage classes have long names, so abbreviate them here:
        Conditional = DecisionCoverageConditional
        Switch = DecisionCoverageSwitch
        Uncheckable = DecisionCoverageUncheckable

        # If decision coverage is not know for one side, return the other.
        if self.decision is None:
            self.decision = decisioncov
        elif decisioncov is None:
            self.decision = Uncheckable()
        # If any decision is Uncheckable, the result is Uncheckable.
        elif isinstance(self.decision, Uncheckable) or isinstance(
            decisioncov, Uncheckable
        ):
            self.decision = Uncheckable()
        # Merge Conditional decisions.
        elif isinstance(self.decision, Conditional) and isinstance(
            decisioncov, Conditional
        ):
            self.decision.count_true += decisioncov.count_true
            self.decision.count_false += decisioncov.count_false
        # Merge Switch decisions.
        elif isinstance(self.decision, Switch) and isinstance(decisioncov, Switch):
            self.decision.count += decisioncov.count
        else:
            self.decision = Uncheckable()

    def insert_branch_coverage(
        self,
        key: int,
        branchcov: BranchCoverage,
        options: MergeOptions = DEFAULT_MERGE_OPTIONS,
    ) -> None:
        """Add a branch coverage item, merge if needed."""
        if key in self.branches:
            self.branches[key].merge(branchcov, options, None)
        else:
            self.branches[key] = branchcov

    def insert_condition_coverage(
        self,
        key: int,
        conditioncov: ConditionCoverage,
        options: MergeOptions = DEFAULT_MERGE_OPTIONS,
    ) -> None:
        """Add a condition coverage item, merge if needed."""
        if key in self.conditions:
            self.conditions[key].merge(conditioncov, options, None)
        else:
            self.conditions[key] = conditioncov

    def insert_decision_coverage(
        self,
        decisioncov: Optional[DecisionCoverage],
    ) -> None:
        """Add a condition coverage item, merge if needed."""
        self.__merge_decision(decisioncov)

    def insert_call_coverage(
        self,
        callcov: CallCoverage,
        options: MergeOptions = DEFAULT_MERGE_OPTIONS,
    ) -> None:
        """Add a branch coverage item, merge if needed."""
        key = callcov.callno
        if key in self.calls:
            self.calls[key].merge(callcov, options, None)
        else:
            self.calls[key] = callcov

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
        self.functions = CoverageDict[str, FunctionCoverage]()
        self.lines = CoverageDict[int, LineCoverage]()
        self.data_sources = (
            set[str]()
            if data_source is None
            else set[str](
                [data_source] if isinstance(data_source, str) else data_source
            )
        )

    def merge(
        self,
        other: FileCoverage,
        options: MergeOptions,
        context: Optional[str],
    ) -> None:
        """
        Merge FileCoverage information.

        Do not use 'other' objects afterwards!

        Precondition: both objects have same filename.
        """

        if self.filename != other.filename:
            raise AssertionError("Filename must be equal")
        if context is not None:
            raise AssertionError("For a file the context must not be set.")

        try:
            self.lines.merge(other.lines, options, self.filename)
            self.functions.merge(other.functions, options, self.filename)
            if other.data_sources:
                self.data_sources.update(other.data_sources)
        except AssertionError as exc:
            message = [str(exc)]
            if other.data_sources:
                message += (
                    "GCOV source files of merge source is/are:",
                    *[f"\t{e}" for e in sorted(other.data_sources)],
                )
            if self.data_sources:
                message += (
                    "and of merge target is/are:",
                    *[f"\t{e}" for e in sorted(self.data_sources)],
                )
            raise AssertionError("\n".join(message)) from None

    def insert_line_coverage(
        self,
        linecov: LineCoverage,
        options: MergeOptions = DEFAULT_MERGE_OPTIONS,
    ) -> LineCoverage:
        """Add a line coverage item, merge if needed."""
        key = linecov.lineno
        if key in self.lines:
            self.lines[key].merge(linecov, options, None)
        else:
            self.lines[key] = linecov

        return self.lines[key]

    def insert_function_coverage(
        self,
        functioncov: FunctionCoverage,
        options: MergeOptions = DEFAULT_MERGE_OPTIONS,
    ) -> None:
        """Add a function coverage item, merge if needed."""
        key = functioncov.name or functioncov.demangled_name
        if key in self.functions:
            self.functions[key].merge(functioncov, options, self.filename)
        else:
            self.functions[key] = functioncov

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

        filecov.lines = CoverageDict[int, LineCoverage](
            {
                lineno: linecov
                for lineno, linecov in self.lines.items()
                if linecov.function_name == functioncov.name
            }
        )

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
