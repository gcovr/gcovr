# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

from .utils import calculate_coverage

# for type annotations:
if False: from typing import (  # noqa, pylint: disable=all
    Callable, Dict, Iterable, List, Optional, Tuple,
)


class BranchCoverage(object):
    r"""Represent coverage information about a branch.

    Args:
        count (int):
            Number of times this branch was followed.
        fallthrough (bool, optional):
            Whether this is a fallthrough branch. None if unknown.
        throw (bool, optional):
            Whether this is an exception-handling branch. None if unknown.
    """

    __slots__ = 'count', 'fallthrough', 'throw'

    def __init__(self, count, fallthrough=None, throw=None):
        # type: (int, Optional[bool], Optional[bool]) -> None
        assert count >= 0

        self.count = count
        self.fallthrough = fallthrough
        self.throw = throw

    @property
    def is_covered(self):
        # type: () -> bool
        return self.count > 0

    def update(self, other):
        # type: (BranchCoverage) -> None
        r"""Merge BranchCoverage information"""
        self.count += other.count
        if other.fallthrough is not None:
            self.fallthrough = other.fallthrough
        if other.throw is not None:
            self.throw = other.throw


class LineCoverage(object):
    r"""Represent coverage information about a line.

    Args:
        lineno (int):
            The line number.
        count (int):
            How often this line was executed at least partially.
        noncode (bool, optional):
            Whether any coverage info on this line should be ignored.
    """

    __slots__ = 'lineno', 'count', 'noncode', 'branches'

    def __init__(self, lineno, count=0, noncode=False):
        # type: (int, int, bool) -> None
        assert lineno > 0
        assert count >= 0

        self.lineno = lineno  # type: int
        self.count = count  # type: int
        self.noncode = noncode
        self.branches = {}  # type: Dict[int, BranchCoverage]

    @property
    def is_covered(self):
        # type: () -> bool
        if self.noncode:
            return False
        return self.count > 0

    @property
    def is_uncovered(self):
        # type: () -> bool
        if self.noncode:
            return False
        return self.count == 0

    def branch(self, branch_id):
        # type: (int) -> BranchCoverage
        r"""Get or create the BranchCoverage for that branch_id."""
        try:
            return self.branches[branch_id]
        except KeyError:
            self.branches[branch_id] = branch_cov = BranchCoverage(0)
            return branch_cov

    def update(self, other):
        # type: (LineCoverage) -> None
        r"""Merge LineCoverage information."""
        assert self.lineno == other.lineno
        self.count += other.count
        self.noncode &= other.noncode
        for branch_id, branch_cov in other.branches.items():
            self.branch(branch_id).update(branch_cov)

    def branch_coverage(self):
        # type: () -> Tuple[int, int, Optional[float]]
        total = len(self.branches)
        cover = 0
        for branch in self.branches.values():
            if branch.is_covered:
                cover += 1

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, percent


class FileCoverage(object):
    __slots__ = 'filename', 'lines'

    def __init__(self, filename):
        # type: (str) -> None
        self.filename = filename
        self.lines = {}  # type: Dict[int, LineCoverage]

    def line(self, lineno, **defaults):
        # type: (int) -> LineCoverage
        r"""Get or create the LineCoverage for that lineno."""
        try:
            return self.lines[lineno]
        except KeyError:
            self.lines[lineno] = line_cov = LineCoverage(lineno, **defaults)
            return line_cov

    def update(self, other):
        # type: (FileCoverage) -> None
        r"""Merge FileCoverage information."""
        assert self.filename == other.filename
        for lineno, line_cov in other.lines.items():
            self.line(lineno, noncode=True).update(line_cov)

    def uncovered_lines_str(self):
        # type: () -> str
        uncovered_lines = sorted(
            lineno for lineno, line in self.lines.items()
            if line.is_uncovered)

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
            for first, last in _find_consecutive_ranges(uncovered_lines))

    def uncovered_branches_str(self):
        # type: () -> str
        uncovered_lines = sorted(
            lineno for lineno, line in self.lines.items()
            if not all(branch.is_covered for branch in line.branches.values())
        )

        # Don't do any aggregation on branch results
        return ",".join(str(x) for x in uncovered_lines)

    def line_coverage(self):
        # type: () -> Tuple[int, int, Optional[float]]
        total = 0
        cover = 0
        for line in self.lines.values():
            if line.is_covered or line.is_uncovered:
                total += 1
            if line.is_covered:
                cover += 1

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, percent

    def branch_coverage(self):
        # type: () -> Tuple[int, int, Optional[float]]
        total = 0
        cover = 0
        for line in self.lines.values():
            b_total, b_cover, _ = line.branch_coverage()
            total += b_total
            cover += b_cover

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, percent


def _find_consecutive_ranges(items):
    first = last = None
    for item in items:
        if last is None:
            first = last = item
            continue

        if item == (last + 1):
            last = item
            continue

        yield first, last
        first = last = item

    if last is not None:
        yield first, last


def _format_range(first, last):
    if first == last:
        return str(first)
    return "{first}-{last}".format(first=first, last=last)
