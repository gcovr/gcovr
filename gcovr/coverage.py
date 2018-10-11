# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

from .utils import calculate_coverage

# for type annotations:
if False: from typing import List, Dict, Optional  # noqa, pylint: disable=all


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

    def __init__(self, count, fallthrough=None, throw=None):
        # type: (int, Optional[bool], Optional[bool]) -> None
        assert count >= 0

        self.count = count
        self.fallthrough = fallthrough
        self.throw = throw

    @property
    def is_coverered(self):
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
        return self.count > 0

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
        self.noncode |= other.noncode
        for branch_id, branch_cov in other.branches.items():
            self.branch(branch_id).update(branch_cov)


class FileCoverage(object):
    def __init__(self, filename):
        # type: (str) -> None
        self.filename = filename
        self.lines = {}  # type: Dict[int, LineCoverage]

    def line(self, lineno):
        # type: (int) -> LineCoverage
        r"""Get or create the LineCoverage for that lineno."""
        try:
            return self.lines[lineno]
        except KeyError:
            self.lines[lineno] = line_cov = LineCoverage(lineno)
            return line_cov

    def update(self, other):
        # type: (FileCoverage) -> None
        r"""Merge FileCoverage information."""
        assert self.filename == other.filename
        for lineno, line_cov in other.lines.items():
            self.line(lineno).update(line_cov)

    def to_coverage_data(self):
        # type: () -> CoverageData
        noncode = set()
        uncovered = set()
        covered = dict()
        branches = dict()  # type: Dict[int, Dict[int, int]]

        for line_cov in self.lines.values():
            if line_cov.noncode:
                noncode.add(line_cov.lineno)

            if line_cov.is_covered:
                covered[line_cov.lineno] = line_cov.count
            elif not line_cov.noncode:
                uncovered.add(line_cov.lineno)

            line_branches = branches[line_cov.lineno] = {}
            for branch_id, branch_cov in line_cov.branches.items():
                line_branches[branch_id] = branch_cov.count

        coverage = CoverageData(self.filename)
        coverage.update(
            uncovered=uncovered,
            covered=covered,
            branches=branches,
            noncode=noncode,
        )
        return coverage


class CoverageData(object):
    """Container for coverage statistics of one file.
    """

    def __init__(self, fname):
        self.fname = fname
        self.uncovered = set()
        self.covered = dict()
        self.noncode = set()
        self.all_lines = set()
        self.branches = dict()

    def update(self, uncovered, covered, branches, noncode):
        self.all_lines.update(uncovered)
        self.all_lines.update(covered.keys())
        self.uncovered.update(uncovered)
        self.noncode.intersection_update(noncode)
        update_counters(self.covered, covered)
        for k in branches.keys():
            d = self.branches.setdefault(k, {})
            update_counters(d, branches[k])
        self.uncovered.difference_update(self.covered.keys())

    def lines_with_uncovered_branches(self):
        for line in self.branches.keys():
            if any(count == 0 for count in self.branches[line].values()):
                yield line

    def uncovered_str(self, show_branch):
        if show_branch:
            # Don't do any aggregation on branch results
            tmp = list(self.lines_with_uncovered_branches())
            return ",".join(str(x) for x in sorted(tmp))

        if not self.uncovered:
            return ""

        # Walk through the uncovered lines in sorted order.
        # Find blocks of consecutive uncovered lines, and return
        # a string with that information.
        #
        # Should we include noncode lines in the range of lines
        # to be covered???  This simplifies the ranges summary, but it
        # provides a counterintuitive listing.
        return ",".join(
            format_range(first, last)
            for first, last in find_consecutive_ranges(sorted(self.uncovered)))

    def coverage(self, show_branch):
        if show_branch:
            total = 0
            cover = 0
            for line in self.branches.keys():
                for branch in self.branches[line].keys():
                    total += 1
                    cover += 1 if self.branches[line][branch] > 0 else 0
        else:
            total = len(self.all_lines)
            cover = len(self.covered)

        percent = calculate_coverage(cover, total, nan_value=None)
        percent = "--" if percent is None else str(int(percent))
        return (total, cover, percent)


def update_counters(target, source):
    for k in source:
        target[k] = target.get(k, 0) + source[k]


def find_consecutive_ranges(items):
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


def format_range(first, last):
    if first == last:
        return str(first)
    return "{first}-{last}".format(first=first, last=last)
