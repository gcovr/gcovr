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
from collections import OrderedDict
import os
import re
from typing import List, Dict, Iterable, Optional, TypeVar, Union
from dataclasses import dataclass

from .utils import commonpath, realpath, force_unix_separator

_T = TypeVar("_T")


def sort_coverage(
    covdata: CovData,
    show_branch: bool,
    filename_uses_relative_pathname: bool = False,
    by_num_uncovered: bool = False,
    by_percent_uncovered: bool = False,
) -> List[str]:
    """Sort a coverage dict.

    covdata (dict): the coverage dictionary
    show_branch (bool): select branch coverage (True) or line coverage (False)
    filename_uses_relative_pathname (bool): for html, we break down a pathname to the
        relative path, but not for other formats.
    by_num_uncovered, by_percent_uncovered (bool):
        select the sort mode. By default, sort alphabetically.

    returns: the sorted keys
    """
    basedir = commonpath(list(covdata.keys()))

    def coverage_stat(key: str) -> CoverageStat:
        cov = covdata[key]
        if show_branch:
            return cov.branch_coverage()
        return cov.line_coverage()

    def num_uncovered_key(key: str) -> int:
        stat = coverage_stat(key)
        uncovered = stat.total - stat.covered
        return uncovered

    def percent_uncovered_key(key: str) -> float:
        stat = coverage_stat(key)
        covered = stat.covered
        total = stat.total

        if covered:
            return -1.0 * covered / total
        elif total:
            return total
        else:
            return 1e6

    def filename(key: str) -> str:
        return (
            force_unix_separator(os.path.relpath(realpath(key), basedir))
            if filename_uses_relative_pathname
            else key
        )

    if by_num_uncovered:
        key_fn = num_uncovered_key
    elif by_percent_uncovered:
        key_fn = percent_uncovered_key
    else:
        key_fn = filename  # by default, we sort by filename alphabetically

    return sorted(covdata, key=key_fn)


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


class CallCoverage:
    r"""Represent coverage information about a call.

    Args:
        covered (bool):
            Whether the call was performed.
    """

    __slots__ = "covered", "callno"

    def __init__(
        self,
        callno: int,
        covered: bool,
    ) -> None:
        self.covered = covered
        self.callno = callno

    @property
    def is_covered(self) -> bool:
        return self.covered


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
    r"""Represent coverage information about a function.

    The counter is stored as dictionary with the line as key to be able
    to merge function coverage in different ways

    Args:
        name (str):
            The name (signature) of the functions.
        lineno (int):
            The line number.
        count (int):
            How often this function was executed.
        excluded (bool, optional):
            Whether this line is excluded by a marker.
    """

    __slots__ = "name", "count", "excluded"

    def __init__(
        self, name: str, *, lineno: int, count: int, excluded: bool = False
    ) -> None:
        assert count >= 0
        self.name = name
        self.count: Dict[int, int] = {lineno: count}
        self.excluded: Dict[int, bool] = {lineno: excluded}


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
        excluded (bool, optional):
            Whether this line is excluded by a marker.
    """

    __slots__ = (
        "lineno",
        "count",
        "excluded",
        "branches",
        "decision",
        "calls",
    )

    def __init__(self, lineno: int, count: int, excluded: bool = False) -> None:
        assert lineno > 0
        assert count >= 0

        self.lineno: int = lineno
        self.count: int = count
        self.excluded: bool = excluded
        self.branches: Dict[int, BranchCoverage] = {}
        self.decision: Optional[DecisionCoverage] = None
        self.calls: Dict[int, CallCoverage] = {}

    @property
    def is_excluded(self) -> bool:
        return self.excluded

    @property
    def is_reportable(self) -> bool:
        return not self.excluded

    @property
    def is_covered(self) -> bool:
        return self.is_reportable and self.count > 0

    @property
    def is_uncovered(self) -> bool:
        return self.is_reportable and self.count == 0

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
    __slots__ = "filename", "functions", "lines", "parent_key"

    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.functions: Dict[str, FunctionCoverage] = {}
        self.lines: Dict[int, LineCoverage] = {}
        self.parent_key: str = ""

    def function_coverage(self) -> CoverageStat:
        total = 0
        covered = 0

        for function in self.functions.values():
            for lineno, excluded in function.excluded.items():
                if not excluded:
                    total += 1
                    if function.count[lineno] > 0:
                        covered += 1

        return CoverageStat(covered, total)

    def line_coverage(self) -> CoverageStat:
        total = 0
        covered = 0

        for line in self.lines.values():
            if line.is_reportable:
                total += 1
                if line.is_covered:
                    covered += 1

        return CoverageStat(covered, total)

    def branch_coverage(self) -> CoverageStat:
        stat = CoverageStat.new_empty()

        for line in self.lines.values():
            if line.is_reportable:
                stat += line.branch_coverage()

        return stat

    def decision_coverage(self) -> DecisionCoverageStat:
        stat = DecisionCoverageStat.new_empty()

        for line in self.lines.values():
            if line.is_reportable:
                stat += line.decision_coverage()

        return stat

    def call_coverage(self) -> CoverageStat:
        covered = 0
        total = 0

        for line in self.lines.values():
            if len(line.calls) > 0:
                for call in line.calls.values():
                    total += 1
                    if call.is_covered:
                        covered += 1

        return CoverageStat(covered, total)


CovData = Dict[str, FileCoverage]


@dataclass
class DirectoryCoverage:
    dirname: str
    stats: SummarizedStats
    children: Dict[str, Union[DirectoryCoverage, FileCoverage]]
    parent_key: str

    @classmethod
    def new_empty(cls) -> DirectoryCoverage:
        return cls("", SummarizedStats.new_empty(), dict(), "")

    @property
    def filename(self) -> str:
        """Helpful function for when we use this DirectoryCoverage in a union with FileCoverage"""
        return self.dirname

    @staticmethod
    def add_directory_coverage(
        subdirs: CovData_subdirectories,
        root_filter: re.Pattern,
        filecov: FileCoverage,
        dircov: Optional[DirectoryCoverage] = None,
    ) -> None:
        r"""Add a file coverage item to the directory structure and accumulate stats.

        This recursive function will accumulate statistics such that every directory
        above it will know the statistics associated with all files deep within a
        directory structure.

        Args:
            subdirs: The top level data structure for all subdirectories. (can start as empty)
            root_filter: Information about the filter used with the root directory
            filecov: The new file and its statistics
            dircov: For recursive use only, the directory this item was added to.
        """
        if dircov is None:
            key = DirectoryCoverage.directory_key(filecov.filename, root_filter)
            filecov.parent_key = key
        else:
            key = DirectoryCoverage.directory_key(dircov.dirname, root_filter)
            dircov.parent_key = key

        if key:
            if key not in subdirs:
                subdir = DirectoryCoverage.new_empty()
                subdir.dirname = key
                subdir.parent_key = DirectoryCoverage.directory_key(key, root_filter)
                subdirs[key] = subdir

            if dircov is None:
                subdirs[key].children[filecov.filename] = filecov
            else:
                subdirs[key].children[dircov.filename] = dircov

            subdirs[key].stats += SummarizedStats.from_file(filecov)
            DirectoryCoverage.add_directory_coverage(
                subdirs, root_filter, filecov, subdirs[key]
            )

    def line_coverage(self) -> CoverageStat:
        """A simple wrapper function necessary for sort_coverage()."""
        return self.stats.line

    def branch_coverage(self) -> CoverageStat:
        """A simple wrapper function necessary for sort_coverage()."""
        return self.stats.branch

    @staticmethod
    def collapse_subdirectories(
        subdirs: CovData_subdirectories, root_filter: re.Pattern
    ) -> None:
        r"""Loop over all the directories and look for items that have only one child.

        For each occurence, move the orphan up to the parent such that the directory
        appears as a single entry in the parent directory with other items at that level.

        Args:
            subdirs: The dictionary of all subdirectories
            root_filter: Information about the filter used with the root directory
        """
        collapse_dirs = set()
        root_key = DirectoryCoverage.directory_root(subdirs, root_filter)
        for key, value in subdirs.items():
            if (
                isinstance(value, DirectoryCoverage)
                and len(value.children) == 1
                and not key == root_key
            ):
                while True:
                    parent_key = DirectoryCoverage.directory_key(key, root_filter)
                    if parent_key not in collapse_dirs or parent_key == root_key:
                        break

                if parent_key:
                    newchildren = {
                        k: child
                        for k, child in subdirs[parent_key].children.items()
                        if child != value
                    }
                    orphan_key = next(iter(value.children))
                    orphan = value.children[orphan_key]
                    orphan.parent_key = parent_key
                    newchildren[orphan_key] = orphan

                    subdirs[parent_key].children = newchildren
                    collapse_dirs.add(key)

        for key in collapse_dirs:
            del subdirs[key]

    @staticmethod
    def from_covdata(
        covdata: CovData, sorted_keys: Iterable, root_filter: re.Pattern
    ) -> CovData_subdirectories:
        subdirs = OrderedDict()
        for key in sorted_keys:
            filecov = covdata[key]
            DirectoryCoverage.add_directory_coverage(subdirs, root_filter, filecov)
        return subdirs

    @staticmethod
    def directory_key(filename: str, root_filter: re.Pattern):
        filename = filename.replace("\\", os.sep).replace("/", os.sep)
        key = os.path.dirname(filename)
        if root_filter.search(key + os.sep) and key != filename:
            return key
        return None

    @staticmethod
    def directory_root(subdirs: CovData_subdirectories, root_filter: re.Pattern) -> str:
        if not subdirs:
            return os.sep
        key = next(iter(subdirs))
        while True:
            next_key = DirectoryCoverage.directory_key(key, root_filter)
            if not next_key:
                return key
            else:
                key = next_key


CovData_subdirectories = Dict[str, DirectoryCoverage]


@dataclass
class SummarizedStats:
    line: CoverageStat
    branch: CoverageStat
    function: CoverageStat
    decision: DecisionCoverageStat
    call: CoverageStat

    @staticmethod
    def new_empty() -> SummarizedStats:
        return SummarizedStats(
            line=CoverageStat.new_empty(),
            branch=CoverageStat.new_empty(),
            function=CoverageStat.new_empty(),
            decision=DecisionCoverageStat.new_empty(),
            call=CoverageStat.new_empty(),
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
            call=filecov.call_coverage(),
        )

    def __iadd__(self, other: SummarizedStats) -> SummarizedStats:
        self.line += other.line
        self.branch += other.branch
        self.function += other.function
        self.decision += other.decision
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
