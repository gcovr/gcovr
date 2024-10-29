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
import os
import re
from typing import (
    List,
    Dict,
    Iterable,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    Literal,
)

from dataclasses import dataclass

from .utils import commonpath, force_unix_separator

LOGGER = logging.getLogger("gcovr")

_T = TypeVar("_T")


def sort_coverage(
    covdata: Union[Dict[str, FileCoverage], Dict[str, DirectoryCoverage]],
    sort_key: Literal["filename", "uncovered-number", "uncovered-percent"],
    sort_reverse: bool,
    by_metric: Literal["line", "branch", "decision"],
    filename_uses_relative_pathname: bool = False,
) -> List[str]:
    """Sort a coverage dict.

    covdata (dict): the coverage dictionary
    sort_key ("filename", "uncovered-number", "uncovered-percent"): the values to sort by
    sort_reverse (bool): reverse order if True
    by_metric ("line", "branch", "decision"): select the metric to sort
    filename_uses_relative_pathname (bool): for html, we break down a pathname to the
        relative path, but not for other formats.

    returns: the sorted keys
    """

    basedir = commonpath(list(covdata.keys()))

    def key_filename(key: str) -> List[str]:
        def convert_to_int_if_possible(text):
            return int(text) if text.isdigit() else text

        key = (
            force_unix_separator(
                os.path.relpath(os.path.realpath(key), os.path.realpath(basedir))
            )
            if filename_uses_relative_pathname
            else key
        ).casefold()

        return [convert_to_int_if_possible(part) for part in re.split(r"([0-9]+)", key)]

    def coverage_stat(key: str) -> CoverageStat:
        cov = covdata[key]
        if by_metric == "branch":
            return cov.branch_coverage()
        if by_metric == "decision":
            return cov.decision_coverage().to_coverage_stat
        return cov.line_coverage()

    def key_num_uncovered(key: str) -> int:
        stat = coverage_stat(key)
        uncovered = stat.total - stat.covered
        return uncovered

    def key_percent_uncovered(key: str) -> float:
        stat = coverage_stat(key)
        covered = stat.covered
        total = stat.total

        # No branches are always put directly after (or before when reversed)
        # files with 100% coverage (by assigning such files 110% coverage)
        return covered / total if total > 0 else 1.1

    if sort_key == "uncovered-number":
        # First sort filename alphabetical and then by the requested key
        return sorted(
            sorted(covdata, key=key_filename),
            key=key_num_uncovered,
            reverse=sort_reverse,
        )
    if sort_key == "uncovered-percent":
        # First sort filename alphabetical and then by the requested key
        return sorted(
            sorted(covdata, key=key_filename),
            key=key_percent_uncovered,
            reverse=sort_reverse,
        )

    # By default, we sort by filename alphabetically
    return sorted(covdata, key=key_filename, reverse=sort_reverse)


class BranchCoverage:
    r"""Represent coverage information about a branch.

    Args:
        blockno (int):
            The block number.
        count (int):
            Number of times this branch was followed.
        fallthrough (bool, optional):
            Whether this is a fallthrough branch. False if unknown.
        throw (bool, optional):
            Whether this is an exception-handling branch. False if unknown.
        destination_blockno (int, optional):
            The destination block of the branch. None if unknown.
        excluded (bool, optional):
            Whether the branch is excluded.
    """

    first_undefined_blockno: bool = True

    __slots__ = (
        "blockno",
        "count",
        "fallthrough",
        "throw",
        "destination_blockno",
        "excluded",
    )

    def __init__(
        self,
        blockno: Optional[int],
        count: int,
        fallthrough: bool = False,
        throw: bool = False,
        destination_blockno: Optional[int] = None,
        excluded: Optional[bool] = None,
    ) -> None:
        if count < 0:
            raise AssertionError("count must not be a negative value.")

        self.blockno = blockno
        self.count = count
        self.fallthrough = fallthrough
        self.throw = throw
        self.destination_blockno = destination_blockno
        self.excluded = excluded

    @property
    def blockno_or_0(self) -> int:
        """Get a valid block number (0) if there was no definition in GCOV file."""
        if self.blockno is None:
            self.blockno = 0
            if BranchCoverage.first_undefined_blockno:
                BranchCoverage.first_undefined_blockno = False
                LOGGER.info("No block number defined, assuming 0 for all undefined")

        return self.blockno

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
        not_covered_true List[int]:
            The conditions which were not true.
        not_covered_false List[int]:
            The conditions which were not false.
        excluded (bool, optional):
            Whether the condition is excluded.
    """

    __slots__ = "count", "covered", "not_covered_true", "not_covered_false", "excluded"

    def __init__(
        self,
        count: int,
        covered: int,
        not_covered_true: List[int],
        not_covered_false: List[int],
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
        start: Optional[Tuple[int, int]] = None,
        end: Optional[Tuple[int, int]] = None,
        excluded: bool = False,
    ) -> None:
        if count < 0:
            raise AssertionError("count must not be a negative value.")
        self.name = name
        self.demangled_name = demangled_name
        self.count: Dict[int, int] = {lineno: count}
        self.blocks: Dict[int, float] = {lineno: blocks}
        self.excluded: Dict[int, bool] = {lineno: excluded}
        self.start: Optional[Dict[int, Tuple[int, int]]] = (
            None if start is None else {lineno: start}
        )
        self.end: Optional[Dict[int, Tuple[int, int]]] = (
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
        block_ids: Optional[List[int]] = None,
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
        self.block_ids: Optional[List[int]] = block_ids
        self.md5: Optional[str] = md5
        self.excluded: bool = excluded
        self.branches: Dict[int, BranchCoverage] = {}
        self.conditions: Dict[int, ConditionCoverage] = {}
        self.decision: Optional[DecisionCoverage] = None
        self.calls: Dict[int, CallCoverage] = {}

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

    __slots__ = "filename", "functions", "lines", "parent_dirname", "data_sources"

    def __init__(
        self, filename: str, data_source: Optional[Union[str, Set[str]]]
    ) -> None:
        self.filename: str = filename
        self.functions: Dict[str, FunctionCoverage] = {}
        self.lines: Dict[int, LineCoverage] = {}
        self.parent_dirname: Optional[str] = None
        self.data_sources: Set[str] = (
            set([])
            if data_source is None
            else set([data_source] if isinstance(data_source, str) else data_source)
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


CovData = Dict[str, FileCoverage]


class DirectoryCoverage:
    """Represent coverage information about a directory."""

    __slots__ = "dirname", "parent_dirname", "children", "stats"

    def __init__(self, dirname: str) -> None:
        self.dirname: str = dirname
        self.parent_dirname: Optional[str] = None
        self.children: Union[CovData, CovDataDirectories] = {}
        self.stats: SummarizedStats = SummarizedStats.new_empty()

    @staticmethod
    def _get_dirname(filename: str, root_filter: re.Pattern):
        filename = filename.replace("\\", os.sep).replace("/", os.sep).rstrip(os.sep)
        dirname = os.path.dirname(filename)
        if root_filter.search(dirname + os.sep) and dirname != filename:
            return dirname + os.sep
        return None

    @staticmethod
    def directory_root(subdirs: CovDataDirectories) -> str:
        """Get the root directory."""
        if not subdirs:
            return os.sep
        # The first directory is the shortest one --> This is the root dir
        return next(iter(sorted(subdirs.keys())))

    @staticmethod
    def from_covdata(
        covdata: CovData, sorted_keys: Iterable, root_filter: re.Pattern
    ) -> CovDataDirectories:
        r"""Add a file coverage item to the directory structure and accumulate stats.

        This recursive function will accumulate statistics such that every directory
        above it will know the statistics associated with all files deep within a
        directory structure.

        Args:
            covdata: The file coverage statistics to get the directory coverage from
            sorted_keys: The sorted keys for covdata
            root_filter: Information about the filter used with the root directory
        """

        dirname_root = None
        subdirs: CovDataDirectories = {}
        for key in sorted_keys:
            filecov = covdata[key]
            dircov: Union[FileCoverage, DirectoryCoverage] = filecov
            while True:
                dirname = DirectoryCoverage._get_dirname(dircov.filename, root_filter)
                if dirname is None:
                    dirname_root = dircov.filename
                    break
                dircov.parent_dirname = dirname
                if dirname not in subdirs:
                    subdirs[dirname] = DirectoryCoverage(dirname)
                subdirs[dirname].children[dircov.filename] = dircov  # type: ignore [assignment]
                subdirs[dirname].stats += SummarizedStats.from_file(filecov)
                dircov = subdirs[dirname]

        collapse_dirs = set()
        for dirname, covdata_directory in subdirs.items():
            if (
                isinstance(covdata_directory, DirectoryCoverage)
                and len(covdata_directory.children) == 1
            ):
                parent_dirname = covdata_directory.parent_dirname
                # Get the key and value of the only child
                orphan_key = next(iter(covdata_directory.children))
                orphan_value = covdata_directory.children[orphan_key]
                # Change the parent key
                orphan_value.parent_dirname = parent_dirname
                if dirname == dirname_root:
                    # The only child is not a File object
                    if not isinstance(orphan_value, FileCoverage):
                        # Replace the children with the orphan ones
                        covdata_directory.children = orphan_value.children
                        # Change the parent key of each new child element
                        for (
                            new_child_key,
                            new_child_value,
                        ) in covdata_directory.children.items():
                            new_child_value.parent_dirname = dirname
                            if isinstance(new_child_value, DirectoryCoverage):
                                subdirs[new_child_key].parent_dirname = dirname
                        # Mark the key for removal.
                        collapse_dirs.add(orphan_key)
                else:
                    # Add orphan value to the parent
                    subdirs[str(parent_dirname)].children[orphan_key] = orphan_value  # type: ignore [assignment]
                    # and remove the current one.
                    subdirs[str(parent_dirname)].children.pop(dirname)
                    # Mark the key for removal.
                    collapse_dirs.add(dirname)

        for dirname in collapse_dirs:
            del subdirs[dirname]

        return subdirs

    @property
    def filename(self) -> str:
        """Helpful function for when we use this DirectoryCoverage in a union with FileCoverage"""
        return self.dirname

    def line_coverage(self) -> CoverageStat:
        """A simple wrapper function necessary for sort_coverage()."""
        return self.stats.line

    def branch_coverage(self) -> CoverageStat:
        """A simple wrapper function necessary for sort_coverage()."""
        return self.stats.branch

    def decision_coverage(self) -> DecisionCoverageStat:
        """A simple wrapper function necessary for sort_coverage()."""
        return self.stats.decision


CovDataDirectories = Dict[str, DirectoryCoverage]


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

    @staticmethod
    def from_covdata(covdata: CovData) -> SummarizedStats:
        """Create a coverage statistic from a coverage data object."""
        stats = SummarizedStats.new_empty()
        for filecov in covdata.values():
            stats += SummarizedStats.from_file(filecov)
        return stats

    @staticmethod
    def from_file(filecov: FileCoverage) -> SummarizedStats:
        """Create a coverage statistic of a file coverage object."""
        return SummarizedStats(
            line=filecov.line_coverage(),
            branch=filecov.branch_coverage(),
            condition=filecov.condition_coverage(),
            decision=filecov.decision_coverage(),
            function=filecov.function_coverage(),
            call=filecov.call_coverage(),
        )

    def __iadd__(self, other: SummarizedStats) -> SummarizedStats:
        self.line += other.line
        self.branch += other.branch
        self.condition += other.condition
        self.decision += other.decision
        self.function += other.function
        self.call += other.call
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
        """Create a empty coverage statistic."""
        return CoverageStat(0, 0)

    @property
    def percent(self) -> Optional[float]:
        """Percentage of covered elements, equivalent to ``self.percent_or(None)``"""
        return self.percent_or(None)

    def percent_or(self, default: _T) -> Union[float, _T]:
        """Percentage of covered elements.

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
        """Create a empty decision coverage statistic."""
        return cls(0, 0, 0)

    @property
    def to_coverage_stat(self) -> CoverageStat:
        """Convert a decision coverage statistic to a coverage statistic."""
        return CoverageStat(covered=self.covered, total=self.total)

    @property
    def percent(self) -> Optional[float]:
        """Return the percent value of the coverage."""
        return self.to_coverage_stat.percent

    def percent_or(self, default: _T) -> Union[float, _T]:
        """Return the percent value of the coverage or the given default if no coverage is present."""
        return self.to_coverage_stat.percent_or(default)

    def __iadd__(self, other: DecisionCoverageStat) -> DecisionCoverageStat:
        self.covered += other.covered
        self.uncheckable += other.uncheckable
        self.total += other.total
        return self
