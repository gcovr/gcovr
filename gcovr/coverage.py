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
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

from .utils import calculate_coverage

# for type annotations:
if False:
    from typing import (  # noqa, pylint: disable=all
        Callable,
        Dict,
        Iterable,
        List,
        Optional,
        Tuple,
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

    __slots__ = "count", "fallthrough", "throw"

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


class DecisionCoverageUncheckable(object):
    r"""Represent coverage information about a decision.

    Args:
        count (int):
            Number of times this decision was made.

    """

    def __init__(self):
        # type: () -> None
        pass

    @property
    def is_uncheckable(self):
        # type: () -> bool
        return True

    @property
    def is_conditional(self):
        # type: () -> bool
        return False

    @property
    def is_switch(self):
        # type: () -> bool
        return False

    def update(self, other):
        # type: (DecisionCoverageUncheckable) -> None
        r"""Merge DecisionCoverage information"""
        pass


class DecisionCoverageConditional(object):
    r"""Represent coverage information about a decision.

    Args:
        count_true (int):
            Number of times this decision was made.

        count_false (int):
            Number of times this decision was made.

    """

    __slots__ = "count_true", "count_false"

    def __init__(self, count_true, count_false):
        # type: (int, int) -> None
        assert count_true >= 0
        self.count_true = count_true
        assert count_false >= 0
        self.count_false = count_false

    @property
    def is_uncheckable(self):
        # type: () -> bool
        return False

    @property
    def is_conditional(self):
        # type: () -> bool
        return True

    @property
    def is_switch(self):
        # type: () -> bool
        return False

    def update(self, other):
        # type: (DecisionCoverageConditional) -> None
        r"""Merge DecisionCoverage information"""
        self.count_true += other.count_true
        self.count_false += other.count_false


class DecisionCoverageSwitch(object):
    r"""Represent coverage information about a decision.

    Args:
        count (int):
            Number of times this decision was made.
    """

    __slots__ = "count"

    def __init__(self, count):
        # type: (int) -> None
        assert count >= 0
        self.count = count

    @property
    def is_uncheckable(self):
        # type: () -> bool
        return False

    @property
    def is_conditional(self):
        # type: () -> bool
        return False

    @property
    def is_switch(self):
        # type: () -> bool
        return True

    def update(self, other):
        # type: (DecisionCoverageSwitch) -> None
        r"""Merge DecisionCoverage information"""
        self.count += other.count


class FunctionCoverage(object):
    __slots__ = "lineno", "count", "name"

    def __init__(self, name, call_count=0):
        # type: (int, int) -> None
        assert call_count >= 0
        self.count = call_count
        self.lineno = 0
        self.name = name

    def update(self, other):
        # type: (FunctionCoverage) -> None
        r"""Merge FunctionCoverage information"""
        self.count += other.count
        if self.lineno == 0:
            self.lineno = other.lineno
        else:
            assert self.lineno == other.lineno


class LineCoverage(object):
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

    def __init__(self, lineno, count=0, noncode=False, excluded=False):
        # type: (int, int, bool) -> None
        assert lineno > 0
        assert count >= 0

        self.lineno = lineno  # type: int
        self.count = count  # type: int
        self.noncode = noncode
        self.excluded = excluded
        self.branches = {}  # type: Dict[int, BranchCoverage]
        self.decision = None

        # There can be only one (user) function per line but:
        # * (multiple) template instantiations
        # * non explicitly defined destructors, called via base virtual destructor!
        # For that reason we need a dictionary instead of a scalar
        self.functions = {}  # type: Dict[str, FunctionCoverage]

    @property
    def is_excluded(self):
        # type: () -> bool
        return self.excluded

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
        self.excluded |= other.excluded
        for other_function in other.functions.values():
            self.add_function(other_function)
        for branch_id, branch_cov in other.branches.items():
            self.branch(branch_id).update(branch_cov)

        if self.decision is None:
            self.decision = other.decision
        else:
            self.decision.update(other.decision)

    def branch_coverage(self):
        # type: () -> Tuple[int, int, Optional[float]]
        total = len(self.branches)
        cover = 0
        for branch in self.branches.values():
            if branch.is_covered:
                cover += 1

        percent = calculate_coverage(cover, total, nan_value=None)
        return total, cover, percent

    def decision_coverage(self):
        # type: () -> Tuple[int, int, int, Optional[float]]
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


class FileCoverage(object):
    __slots__ = "filename", "functions", "lines"

    def __init__(self, filename):
        # type: (str) -> None
        self.filename = filename
        self.functions = {}  # type: Dict[str, FunctionCoverage]
        self.lines = {}  # type: Dict[int, LineCoverage]

    def line(self, lineno, **defaults):
        # type: (int) -> LineCoverage
        r"""Get or create the LineCoverage for that lineno."""
        try:
            return self.lines[lineno]
        except KeyError:
            self.lines[lineno] = line_cov = LineCoverage(lineno, **defaults)
            return line_cov

    def function(self, function_name):
        # type: (str) -> FunctionCoverage
        r"""Get or create the FunctionCoverage for that function."""
        try:
            return self.functions[function_name]
        except KeyError:
            self.functions[function_name] = function_cov = FunctionCoverage(
                function_name
            )
            return function_cov

    def add_function(self, function):
        assert function is not None
        if function.name in self.functions:
            self.functions[
                function.name
            ].count += (
                function.count
            )  # Add the calls to destructor via base class (virtual destructor)
        else:
            self.functions[function.name] = function

    def update(self, other):
        # type: (FileCoverage) -> None
        r"""Merge FileCoverage information."""
        assert self.filename == other.filename
        for lineno, line_cov in other.lines.items():
            self.line(lineno, noncode=True, excluded=False).update(line_cov)
        for fct_name, fct_cov in other.functions.items():
            self.function(fct_name).update(fct_cov)

    def uncovered_lines_str(self):
        # type: () -> str
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

    def uncovered_branches_str(self):
        # type: () -> str
        uncovered_lines = sorted(
            lineno
            for lineno, line in self.lines.items()
            if not all(branch.is_covered for branch in line.branches.values())
        )

        # Don't do any aggregation on branch results
        return ",".join(str(x) for x in uncovered_lines)

    def function_coverage(self):
        # type: () -> Tuple[int, int, Optional[float]]
        total = len(self.functions.values())
        cover = 0
        for function in self.functions.values():
            cover += 1 if function.count > 0 else 0

        percent = calculate_coverage(cover, total, nan_value=None)

        return total, cover, percent

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

    def decision_coverage(self):
        # type: () -> Tuple[int, int, Optional[float]]
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
