# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 4.2, a parsing and reporting tool for gcov.
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

import os
import re
import sys

from contextlib import contextmanager


class Lazy:
    def __init__(self, fn):
        def load(*args):
            result = fn(*args)

            def reuse_value(*args):
                return result

            self.get = reuse_value
            return result

        self.get = load

    def __call__(self, *args):
        return self.get(*args)


def sort_coverage(
    covdata, show_branch, by_num_uncovered=False, by_percent_uncovered=False
):
    """Sort a coverage dict.

    covdata (dict): the coverage dictionary
    show_branch (bool): select branch coverage (True) or line coverage (False)
    by_num_uncovered, by_percent_uncovered (bool):
        select the sort mode. By default, sort alphabetically.

    returns: the sorted keys
    """

    def num_uncovered_key(key):
        cov = covdata[key]
        (total, covered, _) = (
            cov.branch_coverage() if show_branch else cov.line_coverage()
        )
        uncovered = total - covered
        return uncovered

    def percent_uncovered_key(key):
        cov = covdata[key]
        (total, covered, _) = (
            cov.branch_coverage() if show_branch else cov.line_coverage()
        )
        if covered:
            return -1.0 * covered / total
        elif total:
            return total
        else:
            return 1e6

    if by_num_uncovered:
        key_fn = num_uncovered_key
    elif by_percent_uncovered:
        key_fn = percent_uncovered_key
    else:
        key_fn = None  # default key, sort alphabetically

    return sorted(covdata, key=key_fn)


@contextmanager
def open_text_for_writing(filename=None, default_filename=None, **kwargs):
    """Context manager to open and close a file for text writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.endswith(os.sep):
        filename += default_filename

    if filename is not None and filename != "-":
        fh = open(filename, "w", **kwargs)
        close = True
    else:
        fh = sys.stdout
        close = False

    try:
        yield fh
    finally:
        if close:
            fh.close()


@contextmanager
def open_binary_for_writing(filename=None, default_filename=None, **kwargs):
    """Context manager to open and close a file for binary writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename is not None and filename.endswith(os.sep):
        filename += default_filename

    if filename is not None and filename != "-":
        # files in write binary mode for UTF-8
        fh = open(filename, "wb", **kwargs)
        close = True
    else:
        fh = sys.stdout.buffer
        close = False

    try:
        yield fh
    finally:
        if close:
            fh.close()


def presentable_filename(filename, root_filter):
    # type: (str, re.Regex) -> str
    """mangle a filename so that it is suitable for a report"""

    normalized = root_filter.sub("", filename)
    if filename.endswith(normalized):
        # remove any slashes between the removed prefix and the normalized name
        if filename != normalized:
            while normalized.startswith(os.path.sep):
                normalized = normalized[len(os.path.sep) :]
    else:
        # Do no truncation if the filter does not start matching
        # at the beginning of the string
        normalized = filename

    return normalized.replace("\\", "/")


def fixup_percent(percent):
    # output csv percent values in range [0,1.0]
    return percent / 100 if percent is not None else None


def summarize_file_coverage(coverage, root_filter):
    filename = presentable_filename(coverage.filename, root_filter=root_filter)

    branch_total, branch_covered, branch_percent = coverage.branch_coverage()
    line_total, line_covered, line_percent = coverage.line_coverage()
    return (
        filename,
        line_total,
        line_covered,
        fixup_percent(line_percent),
        branch_total,
        branch_covered,
        fixup_percent(branch_percent),
    )


def get_global_stats(covdata):
    r"""Get the global statistics"""
    lines_total = 0
    lines_covered = 0
    branches_total = 0
    branches_covered = 0

    keys = list(covdata.keys())

    for key in keys:
        (total, covered, _) = covdata[key].line_coverage()
        lines_total += total
        lines_covered += covered

        (total, covered, _) = covdata[key].branch_coverage()
        branches_total += total
        branches_covered += covered

    percent = calculate_coverage(lines_covered, lines_total)
    percent_branches = calculate_coverage(branches_covered, branches_total)

    return (
        lines_total,
        lines_covered,
        percent,
        branches_total,
        branches_covered,
        percent_branches,
    )


def calculate_coverage(covered, total, nan_value=0.0):
    r"""Calculate the coverage. Return only 100.0 if all branches are covered."""
    coverage = nan_value
    if total != 0:
        coverage = round(100.0 * covered / total, 1)
        # If we get 100.0% and not all branches are covered use 99.9%
        if (coverage == 100.0) and (covered != total):
            coverage = 99.9

    return coverage
