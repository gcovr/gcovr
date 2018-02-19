# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import copy

from .utils import calculate_coverage


#
# Container object for coverage statistics
#
class CoverageData(object):

    def __init__(
            self, fname, uncovered, uncovered_exceptional, covered, branches,
            noncode):
        self.fname = fname
        # Shallow copies are cheap & "safe" because the caller will
        # throw away their copies of covered & uncovered after calling
        # us exactly *once*
        self.uncovered = copy.copy(uncovered)
        self.uncovered_exceptional = copy.copy(uncovered_exceptional)
        self.covered = copy.copy(covered)
        self.noncode = copy.copy(noncode)
        # But, a deep copy is required here
        self.all_lines = copy.deepcopy(uncovered)
        self.all_lines.update(uncovered_exceptional)
        self.all_lines.update(covered.keys())
        self.branches = copy.deepcopy(branches)

    def update(
            self, uncovered, uncovered_exceptional, covered, branches,
            noncode):
        self.all_lines.update(uncovered)
        self.all_lines.update(uncovered_exceptional)
        self.all_lines.update(covered.keys())
        self.uncovered.update(uncovered)
        self.uncovered_exceptional.update(uncovered_exceptional)
        self.noncode.intersection_update(noncode)
        for k in covered.keys():
            self.covered[k] = self.covered.get(k, 0) + covered[k]
        for k in branches.keys():
            for b in branches[k]:
                d = self.branches.setdefault(k, {})
                d[b] = d.get(b, 0) + branches[k][b]
        self.uncovered.difference_update(self.covered.keys())
        self.uncovered_exceptional.difference_update(self.covered.keys())

    def uncovered_str(self, exceptional, show_branch):
        if show_branch:
            #
            # Don't do any aggregation on branch results
            #
            tmp = []
            for line in self.branches.keys():
                for branch in self.branches[line]:
                    if self.branches[line][branch] == 0:
                        tmp.append(line)
                        break
            tmp.sort()
            return ",".join([str(x) for x in tmp]) or ""

        if exceptional:
            tmp = list(self.uncovered_exceptional)
        else:
            tmp = list(self.uncovered)
        if len(tmp) == 0:
            return ""

        #
        # Walk through the uncovered lines in sorted order.
        # Find blocks of consecutive uncovered lines, and return
        # a string with that information.
        #
        tmp.sort()
        first = None
        last = None
        ranges = []
        for item in tmp:
            if last is None:
                first = item
                last = item
            elif item == (last + 1):
                last = item
            else:
                #
                # Should we include noncode lines in the range of lines
                # to be covered???  This simplifies the ranges summary, but it
                # provides a counterintuitive listing.
                #
                # if len(self.noncode.intersection(range(last+1,item))) \
                #        == item - last - 1:
                #     last = item
                #     continue
                #
                if first == last:
                    ranges.append(str(first))
                else:
                    ranges.append(str(first) + "-" + str(last))
                first = item
                last = item
        if first == last:
            ranges.append(str(first))
        else:
            ranges.append(str(first) + "-" + str(last))
        return ",".join(ranges)

    def coverage(self, show_branch):
        if show_branch:
            total = 0
            cover = 0
            for line in self.branches.keys():
                for branch in self.branches[line].keys():
                    total += 1
                    cover += self.branches[line][branch] > 0 and 1 or 0
        else:
            total = len(self.all_lines)
            cover = len(self.covered)

        percent = calculate_coverage(cover, total, nan_value=None)
        percent = "--" if percent is None else str(int(percent))
        return (total, cover, percent)
