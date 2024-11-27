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

from typing import Iterable

from ...options import Options

from ...utils import (
    force_unix_separator,
    presentable_filename,
    open_text_for_writing,
)
from ...coverage import (
    CoverageContainer,
    CoverageStat,
    FileCoverage,
)

# Widths of the various columns
COL_FILE_WIDTH = 40
COL_TOTAL_COUNT_WIDTH = 8
COL_COVERED_COUNT_WIDTH = 8
COL_PERCENTAGE_WIDTH = 7  # including "%" percentage sign
UN_COVERED_SEPARATOR = "   "
LINE_WIDTH = 78


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce the classic gcovr text report"""

    with open_text_for_writing(output_file, "coverage.txt") as fh:
        # Header
        fh.write("-" * LINE_WIDTH + "\n")
        fh.write("GCC Code Coverage Report".center(LINE_WIDTH).rstrip() + "\n")
        # fh.write(" " * 27 + "GCC Code Coverage Report\n")
        fh.write("Directory: " + force_unix_separator(options.root) + "\n")

        fh.write("-" * LINE_WIDTH + "\n")
        if options.txt_metric == "branch":
            title_total = "Branches"
            title_covered = "Taken"
        elif options.txt_metric == "decision":
            title_total = "Decisions"
            title_covered = "Taken"
        else:
            title_total = "Lines"
            title_covered = "Exec"

        title_percentage = "Cover"
        title_un_covered = "Covered" if options.txt_report_covered else "Missing"
        fh.write(
            "File".ljust(COL_FILE_WIDTH)
            + title_total.rjust(COL_TOTAL_COUNT_WIDTH)
            + title_covered.rjust(COL_COVERED_COUNT_WIDTH)
            + title_percentage.rjust(COL_PERCENTAGE_WIDTH)
            + UN_COVERED_SEPARATOR
            + title_un_covered
            + "\n"
        )
        fh.write("-" * LINE_WIDTH + "\n")

        # Data
        sorted_keys = covdata.sort_coverage(
            sort_key=options.sort_key,
            sort_reverse=options.sort_reverse,
            by_metric=options.txt_metric,
        )

        total_stat = CoverageStat.new_empty()
        for key in sorted_keys:
            (stat, txt) = _summarize_file_coverage(covdata[key], options)
            total_stat += stat
            fh.write(txt + "\n")

        # Footer & summary
        fh.write("-" * LINE_WIDTH + "\n")
        fh.write(_format_line("TOTAL", total_stat, "") + "\n")
        fh.write("-" * LINE_WIDTH + "\n")


def write_summary_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """Print a small report to the standard output.
    Output the percentage, covered and total lines and branches.
    """

    with open_text_for_writing(output_file, "coverage.txt") as fh:

        def print_stat(name: str, stat: CoverageStat) -> None:
            percent = stat.percent_or(0.0)
            covered = stat.covered
            total = stat.total
            fh.write(f"{name}: {percent:0.1f}% ({covered} out of {total})\n")

        stats = covdata.stats
        print_stat("lines", stats.line)
        print_stat("functions", stats.function)
        print_stat("branches", stats.branch)
        if stats.condition.total != 0:
            print_stat("conditions", stats.condition)
        if options.show_decision:
            print_stat("decisions", stats.decision.to_coverage_stat)
        if not options.exclude_calls:
            print_stat("calls", stats.call)


def _summarize_file_coverage(
    coverage: FileCoverage, options: Options
) -> tuple[CoverageStat, str]:
    filename = presentable_filename(coverage.filename, root_filter=options.root_filter)

    if options.txt_report_covered:
        if options.txt_metric == "branch":
            stat = coverage.branch_coverage()
            covered_lines = _covered_branches_str(coverage)
        elif options.txt_metric == "decision":
            stat = coverage.decision_coverage().to_coverage_stat
            covered_lines = _covered_decisions_str(coverage)
        else:
            stat = coverage.line_coverage()
            covered_lines = _covered_lines_str(coverage)

        return stat, _format_line(filename, stat, covered_lines)

    if options.txt_metric == "branch":
        stat = coverage.branch_coverage()
        uncovered_lines = _uncovered_branches_str(coverage)
    elif options.txt_metric == "decision":
        stat = coverage.decision_coverage().to_coverage_stat
        uncovered_lines = _uncovered_decisions_str(coverage)
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
        line += UN_COVERED_SEPARATOR + uncovered_lines

    return line


def _covered_lines_str(filecov: FileCoverage) -> str:
    covered_lines = sorted(
        linecov.lineno for linecov in filecov.lines.values() if not linecov.is_uncovered
    )

    # Walk through the covered lines in sorted order.
    # Find blocks of consecutive uncovered lines, and return
    # a string with that information.
    #
    # Should we exclude noncode lines in the range of lines
    # to be covered???  This simplifies the ranges summary, but it
    # provides a counterintuitive listing.
    return ",".join(
        _format_range(first, last)
        for first, last in _find_consecutive_ranges(covered_lines)
    )


def _uncovered_lines_str(filecov: FileCoverage) -> str:
    uncovered_lines = sorted(
        linecov.lineno for linecov in filecov.lines.values() if linecov.is_uncovered
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


def _covered_branches_str(filecov: FileCoverage) -> str:
    covered_lines = sorted(
        linecov.lineno
        for linecov in filecov.lines.values()
        if not linecov.has_uncovered_branch
    )

    # Don't do any aggregation on branch results.
    return ",".join(str(lineno) for lineno in covered_lines)


def _covered_decisions_str(filecov: FileCoverage) -> str:
    covered_decisions = sorted(
        linecov.lineno
        for linecov in filecov.lines.values()
        if not linecov.has_uncovered_decision
    )
    return ",".join(str(lineno) for lineno in covered_decisions)


def _uncovered_decisions_str(filecov: FileCoverage) -> str:
    uncovered_decisions = sorted(
        linecov.lineno
        for linecov in filecov.lines.values()
        if linecov.has_uncovered_decision
    )
    return ",".join(str(lineno) for lineno in uncovered_decisions)


def _uncovered_branches_str(filecov: FileCoverage) -> str:
    uncovered_lines = sorted(
        linecov.lineno
        for linecov in filecov.lines.values()
        if linecov.has_uncovered_branch
    )

    # Don't do any aggregation on branch results.
    return ",".join(str(lineno) for lineno in uncovered_lines)


def _find_consecutive_ranges(items: Iterable[int]) -> Iterable[tuple[int, int]]:
    first = last = None
    for item in items:
        if last is None:
            first = last = item
            continue

        if item == (last + 1):
            last = item
            continue

        if first is None:  # pragma: no cover
            raise AssertionError("First must not be 'None'")
        yield first, last
        first = last = item

    if last is not None:
        if first is None:  # pragma: no cover
            raise AssertionError("First must not be 'None'")
        yield first, last


def _format_range(first: int, last: int) -> str:
    if first == last:
        return str(first)
    return f"{first}-{last}"
