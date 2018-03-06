# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

from .utils import calculate_coverage


class CoverageData(object):
    """Container for coverage statistics of one file.
    """

    def __init__(self, fname):
        self.fname = fname
        self.uncovered = set()
        self.uncovered_exceptional = set()
        self.covered = dict()
        self.noncode = set()
        self.all_lines = set()
        self.branches = dict()

    def update(
            self, uncovered, uncovered_exceptional, covered, branches,
            noncode):
        self.all_lines.update(uncovered)
        self.all_lines.update(uncovered_exceptional)
        self.all_lines.update(covered.keys())
        self.uncovered.update(uncovered)
        self.uncovered_exceptional.update(uncovered_exceptional)
        self.noncode.intersection_update(noncode)
        update_counters(self.covered, covered)
        for k in branches.keys():
            d = self.branches.setdefault(k, {})
            update_counters(d, branches[k])
        self.uncovered.difference_update(self.covered.keys())
        self.uncovered_exceptional.difference_update(self.covered.keys())

    def lines_with_uncovered_branches(self):
        for line in self.branches.keys():
            if any(count == 0 for count in self.branches[line].values()):
                yield line

    def uncovered_str(self, exceptional, show_branch):
        if show_branch:
            # Don't do any aggregation on branch results
            tmp = list(self.lines_with_uncovered_branches())
            return ",".join(str(x) for x in sorted(tmp))

        if exceptional:
            tmp = list(self.uncovered_exceptional)
        else:
            tmp = list(self.uncovered)
        if len(tmp) == 0:
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
            for first, last in find_consecutive_ranges(sorted(tmp)))

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
