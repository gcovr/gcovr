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

from typing import Iterable, Tuple

from ..utils import (
    sort_coverage,
    presentable_filename,
    open_text_for_writing,
)
from ..coverage import CovData, CoverageStat, FileCoverage

# Widths of the various columns
COL_FILE_WIDTH = 40
COL_TOTAL_COUNT_WIDTH = 8
COL_COVERED_COUNT_WIDTH = 8
COL_PERCENTAGE_WIDTH = 7  # including "%" percentage sign
MISSING_SEPARATOR = "   "
LINE_WIDTH = 78


def print_text_report(covdata: CovData, output_file, options):
    """produce the classic gcovr text report"""

    with open_text_for_writing(output_file, "coverage.txt") as fh:
        # Header
        fh.write("-" * LINE_WIDTH + "\n")
        fh.write("GCC Code Coverage Report".center(LINE_WIDTH).rstrip() + "\n")
        # fh.write(" " * 27 + "GCC Code Coverage Report\n")
        fh.write("Directory: " + options.root.replace("\\", "/") + "\n")

        fh.write("-" * LINE_WIDTH + "\n")
        title_total = "Branches" if options.show_branch else "Lines"
        title_covered = "Taken" if options.show_branch else "Exec"
        title_percentage = "Cover"
        title_missing = "Missing"
        fh.write(
            "File".ljust(COL_FILE_WIDTH)
            + title_total.rjust(COL_TOTAL_COUNT_WIDTH)
            + title_covered.rjust(COL_COVERED_COUNT_WIDTH)
            + title_percentage.rjust(COL_PERCENTAGE_WIDTH)
            + MISSING_SEPARATOR
            + title_missing
            + "\n"
        )
        fh.write("-" * LINE_WIDTH + "\n")

        # Data
        keys = sort_coverage(
            covdata,
            show_branch=options.show_branch,
            by_num_uncovered=options.sort_uncovered,
            by_percent_uncovered=options.sort_percent,
        )

        total_stat = CoverageStat.new_empty()
        for key in keys:
            (stat, txt) = _summarize_file_coverage(covdata[key], options)
            total_stat += stat
            fh.write(txt + "\n")

        # Footer & summary
        fh.write("-" * LINE_WIDTH + "\n")
        fh.write(_format_line("TOTAL", total_stat, "") + "\n")
        fh.write("-" * LINE_WIDTH + "\n")


def _summarize_file_coverage(coverage: FileCoverage, options):
    filename = presentable_filename(coverage.filename, root_filter=options.root_filter)

    if options.show_branch:
        stat = coverage.branch_coverage()
        uncovered_lines = _uncovered_branches_str(coverage)
    else:
        stat = coverage.line_coverage()
        uncovered_lines = _uncovered_lines_str(coverage)

    return stat, _format_line(filename, stat, uncovered_lines)


def _format_line(name: str, stat: CoverageStat, uncovered_lines: str) -> str:
    raw_percent = stat.percent
    if raw_percent is None:
        percent = "--"
    else:
        percent = str(int(raw_percent))

    name = name.ljust(COL_FILE_WIDTH)
    if len(name) > 40:
        name = name + "\n" + " " * COL_FILE_WIDTH

    line = (
        name
        + str(stat.total).rjust(COL_TOTAL_COUNT_WIDTH)
        + str(stat.covered).rjust(COL_COVERED_COUNT_WIDTH)
        + percent.rjust(COL_PERCENTAGE_WIDTH - 1)
        + "%"
    )

    if uncovered_lines:
        line += MISSING_SEPARATOR + uncovered_lines

    return line


def _uncovered_lines_str(filecov: FileCoverage) -> str:
    uncovered_lines = sorted(
        line.lineno for line in filecov.lines.values() if line.is_uncovered
    )

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


def _uncovered_branches_str(filecov: FileCoverage) -> str:
    uncovered_lines = sorted(
        line.lineno for line in filecov.lines.values() if line.has_uncovered_branch
    )

    # Dn't do any aggregation on branch results.
    return ",".join(str(lineno) for lineno in uncovered_lines)


def _find_consecutive_ranges(items: Iterable[int]) -> Iterable[Tuple[int, int]]:
    first = last = None
    for item in items:
        if last is None:
            first = last = item
            continue

        if item == (last + 1):
            last = item
            continue

        assert first is not None
        yield first, last
        first = last = item

    if last is not None:
        assert first is not None
        yield first, last


def _format_range(first: int, last: int) -> str:
    if first == last:
        return str(first)
    return "{first}-{last}".format(first=first, last=last)
