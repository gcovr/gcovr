# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 7.1, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
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
from collections import OrderedDict
import os
import re
from typing import Any, List, Dict, Iterable, Optional, TypeVar, Union, Literal

from dataclasses import dataclass

from .utils import commonpath, force_unix_separator

_T = TypeVar("_T")


def sort_coverage(
    covdata: CovData,
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

    def key_filename(key: str) -> str:
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
        elif by_metric == "decision":
            return cov.decision_coverage()
        return cov.line_coverage()

    def key_num_uncovered(key: str) -> int:
        stat = coverage_stat(key)
        uncovered = stat.total - stat.covered
        return uncovered

    def key_percent_uncovered(key: str) -> float:
        stat = coverage_stat(key)
        covered = stat.covered
        total = stat.total

        if covered:
            # If branches are covered, use the percentage
            value = covered / total
        elif total:
            # If no branches are covered use the number of branches
            # + 1 to be inserted after the covered branches
            value = total
        else:
            # No branches are always put at the end.
            # Hopefully no one has such many branches.
            value = -1 if sort_reverse else 1e99

        return value

    if sort_key == "uncovered-number":
        key_fn = key_num_uncovered
    elif sort_key == "uncovered-percent":
        key_fn = key_percent_uncovered
    else:
        # by default, we sort by filename alphabetically
        return sorted(covdata, key=key_filename, reverse=sort_reverse)

    # First sort filename alphabetical and then by the requested key
    return sorted(sorted(covdata, key=key_filename), key=key_fn, reverse=sort_reverse)


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
    """

    __slots__ = "blockno", "count", "fallthrough", "throw"

    def __init__(
        self,
        blockno: int,
        count: int,
        fallthrough: bool = False,
        throw: bool = False,
    ) -> None:
        assert count >= 0

        self.blockno = blockno
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
        returned (int):
            How often this function returned.
        blocks (float):
            Block coverage of function.
        excluded (bool, optional):
            Whether this line is excluded by a marker.
    """

    __slots__ = "name", "count", "returned", "blocks", "excluded"

    def __init__(
        self,
        name: str,
        *,
        lineno: int,
        count: int,
        returned: int,
        blocks: float,
        excluded: bool = False,
    ) -> None:
        assert count >= 0
        self.name = name
        self.count: Dict[int, int] = {lineno: count}
        self.returned: Dict[int, int] = {lineno: returned}
        self.blocks: Dict[int, int] = {lineno: blocks}
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
        md5 (str):
            The md5 checksum of the source code line.
    """

    __slots__ = (
        "lineno",
        "count",
        "excluded",
        "md5",
        "branches",
        "decision",
        "calls",
    )

    def __init__(
        self, lineno: int, count: int, excluded: bool = False, md5: str = None
    ) -> None:
        assert lineno > 0
        assert count >= 0

        self.lineno: int = lineno
        self.count: int = count
        self.excluded: bool = excluded
        self.md5: str = md5
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

    @property
    def has_uncovered_decision(self) -> bool:
        if self.decision is None:
            return False

        if isinstance(self.decision, DecisionCoverageUncheckable):
            return False

        if isinstance(self.decision, DecisionCoverageConditional):
            return self.decision.count_true == 0 or self.decision.count_false == 0

        if isinstance(self.decision, DecisionCoverageSwitch):
            return self.decision.count == 0

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
    __slots__ = "filename", "functions", "lines", "parent_dirname"

    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.functions: Dict[str, FunctionCoverage] = {}
        self.lines: Dict[int, LineCoverage] = {}
        self.parent_dirname: str = None

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


class DirectoryCoverage:
    __slots__ = "dirname", "parent_dirname", "children", "stats"

    def __init__(self, dirname: str) -> None:
        self.dirname: str = dirname
        self.parent_dirname: DirectoryCoverage = None
        self.children: Dict[str, Any[DirectoryCoverage, FileCoverage]] = {}
        self.stats: SummarizedStats = SummarizedStats.new_empty()

    @staticmethod
    def _get_dirname(filename: str, root_filter: re.Pattern):
        filename = filename.replace("\\", os.sep).replace("/", os.sep).rstrip(os.sep)
        dirname = os.path.dirname(filename)
        if root_filter.search(dirname + os.sep) and dirname != filename:
            return dirname + os.sep
        return None

    @staticmethod
    def directory_root(subdirs: CovData_directories, root_filter: re.Pattern) -> str:
        if not subdirs:
            return os.sep
        # The first directory is the shortest one --> This is the root dir
        return next(iter(sorted(subdirs.keys())))

    @staticmethod
    def from_covdata(
        covdata: CovData, sorted_keys: Iterable, root_filter: re.Pattern
    ) -> CovData_directories:
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
        subdirs: CovData_directories = OrderedDict()
        for key in sorted_keys:
            filecov = covdata[key]
            dircov = filecov
            while True:
                dirname = DirectoryCoverage._get_dirname(dircov.filename, root_filter)
                if dirname is None:
                    dirname_root = dircov.filename
                    break
                dircov.parent_dirname = dirname
                if dirname not in subdirs:
                    subdirs[dirname] = DirectoryCoverage(dirname)
                subdirs[dirname].children[dircov.filename] = dircov
                subdirs[dirname].stats += SummarizedStats.from_file(filecov)
                dircov = subdirs[dirname]

        collapse_dirs = set()
        for dirname, covdata in subdirs.items():
            if isinstance(covdata, DirectoryCoverage) and len(covdata.children) == 1:
                parent_dirname = covdata.parent_dirname
                # Get the key and value of the only child
                orphan_key = next(iter(covdata.children))
                orphan_value = covdata.children[orphan_key]
                # Change the parent key
                orphan_value.parent_dirname = parent_dirname
                if dirname == dirname_root:
                    # The only child is not a File object
                    if not isinstance(orphan_value, FileCoverage):
                        # Replace the children with the orphan ones
                        covdata.children = orphan_value.children
                        # Change the parent key of each new child element
                        for new_child_key, new_child_value in covdata.children.items():
                            new_child_value.parent_dirname = dirname
                            if isinstance(new_child_value, DirectoryCoverage):
                                subdirs[new_child_key].parent_dirname = dirname
                        # Mark the key for removal.
                        collapse_dirs.add(orphan_key)
                else:
                    # Add orphan value to the parent
                    subdirs[parent_dirname].children[orphan_key] = orphan_value
                    # and remove the current one.
                    subdirs[parent_dirname].children.pop(dirname)
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


CovData_directories = Dict[str, DirectoryCoverage]


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
