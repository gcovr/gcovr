# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import re
from typing import Iterable, Literal

from gcovr.exceptions import SanityCheckError

from ...data_model.container import CoverageContainer
from ...data_model.coverage import CoverageDiff, FileCoverage
from ...data_model.stats import CoverageStat
from ...options import Options
from ...utils import force_unix_separator, open_text_for_writing

# Widths of the various columns
COL_FILE_WIDTH = 40
COL_TOTAL_COUNT_WIDTH = 10
COL_COVERED_COUNT_WIDTH = 9
COL_PERCENTAGE_WIDTH = 7  # including "%" percentage sign
COL_DIFF_STATE_WIDTH = 20
SEPARATOR = "   "


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """Produce the classic gcovr text report"""

    all_metrics: list[Literal["line", "branch", "condition", "decision"]] = (
        options.txt_metrics or ["line"]
    )
    single_metric = len(all_metrics) == 1

    diff_report = covdata.is_compare_info_available()
    if diff_report:
        if all_metrics != ["line"]:
            raise RuntimeError(
                "Diff report is only supported for line coverage at this time."
            )

    title_un_covered = "Covered" if options.txt_report_covered else "Missing"

    line_width = (
        COL_FILE_WIDTH
        + (
            (
                COL_TOTAL_COUNT_WIDTH
                + COL_COVERED_COUNT_WIDTH
                + COL_PERCENTAGE_WIDTH
                # Add width of (un)covered lines column if single metric
                + (len(SEPARATOR + title_un_covered) if single_metric else 0)
            )
            * len(all_metrics)
        )
        # Add separators between metrics
        + (len(SEPARATOR) * (len(all_metrics) - 1))
        + 2
    )

    with open_text_for_writing(output_file, "coverage.txt") as fh:
        # Header
        fh.write("-" * line_width + "\n")
        fh.write(
            f"GCC Code Coverage Report{' (Diff mode)' if diff_report else ''}".center(
                line_width
            ).rstrip()
            + "\n"
        )
        # fh.write(" " * 27 + "GCC Code Coverage Report\n")
        fh.write("Directory: " + force_unix_separator(options.root) + "\n")

        fh.write("-" * line_width + "\n")
        fh.write("File".ljust(COL_FILE_WIDTH))
        # Data sorted by first metric.
        filecov_list = covdata.sorted_filecov(
            sort_key=options.sort_key,
            sort_reverse=options.sort_reverse,
            by_metric=all_metrics[0],
            recurse=True,
        )
        if diff_report:
            fh.write("State".rjust(COL_DIFF_STATE_WIDTH) + SEPARATOR + "Lines\n")
            for filecov in filecov_list:
                txt = _diff_report_file(filecov, options.root_filter)
                fh.write(txt + "\n")
        else:
            metrics_as_txt = list[str]()
            for metric in all_metrics:
                if metric == "line":
                    title_total = "Lines"
                    title_covered = "Exec"
                elif metric == "branch":
                    title_total = "Branches"
                    title_covered = "Taken"
                elif metric == "condition":
                    title_total = "Conditions"
                    title_covered = "Taken"
                elif metric == "decision":
                    title_total = "Decisions"
                    title_covered = "Taken"
                else:
                    raise SanityCheckError(f"Unknown metric: {metric}")

                metrics_as_txt.append(
                    title_total.rjust(COL_TOTAL_COUNT_WIDTH)
                    + title_covered.rjust(COL_COVERED_COUNT_WIDTH)
                    + "Cover".rjust(COL_PERCENTAGE_WIDTH)
                    + ((SEPARATOR + title_un_covered) if single_metric else "")
                )
            fh.write(SEPARATOR.join(metrics_as_txt) + "\n")
            fh.write("-" * line_width + "\n")

            total_stat = dict[
                Literal["line", "branch", "condition", "decision"], CoverageStat
            ]()
            for metric in all_metrics:
                total_stat[metric] = CoverageStat.new_empty()
            for filecov in filecov_list:
                filename = filecov.presentable_filename(options.root_filter)
                if len(filename) < COL_FILE_WIDTH:
                    filename = filename.ljust(COL_FILE_WIDTH)
                else:
                    filename = filename + "\n" + " " * COL_FILE_WIDTH
                fh.write(
                    filename
                    + _report_file(options.txt_report_covered, filecov, total_stat)
                    + "\n"
                )

            # Footer & summary
            fh.write("-" * line_width + "\n")
            metrics_as_txt = list[str]()
            for stat in total_stat.values():
                metrics_as_txt.append(_format_line(stat, ""))
            fh.write(
                "TOTAL".ljust(COL_FILE_WIDTH) + SEPARATOR.join(metrics_as_txt) + "\n"
            )
            fh.write("-" * line_width + "\n")


def write_summary_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """Print a small report to the standard output.
    Output the percentage, covered and total lines and branches.
    """

    with open_text_for_writing(output_file, "coverage.txt") as fh:
        if covdata.is_compare_info_available():
            for current_diff in CoverageDiff:
                filecov_list = [
                    filecov
                    for filecov in covdata.filecov(recurse=True)
                    if filecov.diff == current_diff
                ]
                if filecov_list:
                    fh.write(f"{str(current_diff.value).capitalize()} file coverage:\n")
                    for filecov in sorted(
                        filecov_list,
                        key=lambda fc: fc.presentable_filename(options.root_filter),
                    ):
                        fh.write(
                            f"  {filecov.presentable_filename(options.root_filter)}\n"
                        )
        else:

            def print_stat(name: str, stat: CoverageStat) -> None:
                percent = stat.percent_or(0.0)
                covered = stat.covered
                total = stat.total
                fh.write(f"{name}: {percent:0.1f}% ({covered} out of {total})\n")

            print_stat("lines", covdata.line_coverage())
            print_stat("functions", covdata.function_coverage())
            print_stat("branches", covdata.branch_coverage())
            if covdata.condition_coverage().total != 0:
                print_stat("conditions", covdata.condition_coverage())
            if options.show_decision:
                print_stat("decisions", covdata.decision_coverage().to_coverage_stat)
            if options.show_calls:
                print_stat("calls", covdata.call_coverage())


def _diff_report_file(filecov: FileCoverage, root_filter: re.Pattern[str]) -> str:
    filename = filecov.presentable_filename(root_filter)

    filename = filename.ljust(COL_FILE_WIDTH)
    if len(filename) > 40:
        filename = filename + "\n" + " " * COL_FILE_WIDTH

    lines_with_diff = list[str]()
    for current_diff in CoverageDiff:
        # If there which are strict equal we only list them if no other diffs exist
        if current_diff == CoverageDiff.STRICTLY_EQUAL and lines_with_diff:
            continue
        linecov_list = [
            linecov
            for linecov in filecov.linecov(sort=True)
            if linecov.diff == current_diff
        ]
        if linecov_list:
            # Only show line ranges for lines with differences
            # and if the file itself is not added or removed
            line_ranges = (
                ""
                if current_diff
                in (
                    CoverageDiff.UNDEFINED,  # This is the case for added and removed files
                    CoverageDiff.STRICTLY_EQUAL,
                )
                or filecov.diff
                in (
                    CoverageDiff.ADDED,
                    CoverageDiff.REMOVED,
                )
                else ",".join(
                    _format_range(first, last)
                    for first, last in _find_consecutive_ranges(
                        (linecov.lineno for linecov in linecov_list)
                    )
                )
            )
            if lines_with_diff:
                lines_with_diff.append(
                    f"{str(current_diff.value).rjust(COL_FILE_WIDTH + COL_DIFF_STATE_WIDTH)}{SEPARATOR}{line_ranges}"
                )
            else:
                lines_with_diff.append(
                    f"{filename}{str(filecov.diff.value).rjust(COL_DIFF_STATE_WIDTH)}{SEPARATOR}{line_ranges}"
                )

    return "\n".join(lines_with_diff)


def _report_file(
    report_covered: bool,
    filecov: FileCoverage,
    total_stat: dict[Literal["line", "branch", "condition", "decision"], CoverageStat],
) -> str:
    several_metrics = len(total_stat) > 1
    metrics_as_text = list[str]()
    for metric in total_stat.keys():
        if metric == "line":
            stat = filecov.line_coverage()
        elif metric == "branch":
            stat = filecov.branch_coverage()
        elif metric == "condition":
            stat = filecov.condition_coverage()
        elif metric == "decision":
            stat = filecov.decision_coverage().to_coverage_stat
        else:
            raise SanityCheckError(f"Unknown metric: {metric}")

        total_stat[metric] += stat

        if several_metrics:
            lines = ""
        elif report_covered:
            if metric == "line":
                lines = _covered_lines_str(filecov)
            elif metric == "branch":
                lines = _covered_branches_str(filecov)
            elif metric == "condition":
                lines = _covered_conditions_str(filecov)
            elif metric == "decision":
                lines = _covered_decisions_str(filecov)
            else:
                raise SanityCheckError(f"Unknown metric: {metric}")
        else:
            if metric == "line":
                lines = _uncovered_lines_str(filecov)
            elif metric == "branch":
                lines = _uncovered_branches_str(filecov)
            elif metric == "condition":
                lines = _uncovered_conditions_str(filecov)
            elif metric == "decision":
                lines = _uncovered_decisions_str(filecov)
            else:
                raise SanityCheckError(f"Unknown metric: {metric}")

        metrics_as_text.append(_format_line(stat, lines))

    return SEPARATOR.join(metrics_as_text)


def _format_line(stat: CoverageStat, uncovered_lines: str) -> str:
    raw_percent = stat.percent
    if raw_percent is None:
        percent = "--"
    else:
        percent = str(int(raw_percent))

    line = (
        str(stat.total).rjust(COL_TOTAL_COUNT_WIDTH)
        + str(stat.covered).rjust(COL_COVERED_COUNT_WIDTH)
        + percent.rjust(COL_PERCENTAGE_WIDTH - 1)
        + "%"
    )

    if uncovered_lines:
        line += SEPARATOR + uncovered_lines

    return line


def _covered_lines_str(filecov: FileCoverage) -> str:
    covered_lines = (
        linecov.lineno
        for linecov in filecov.linecov(sort=True)
        if not linecov.is_uncovered
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
    uncovered_lines = (
        linecov.lineno for linecov in filecov.linecov(sort=True) if linecov.is_uncovered
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
    covered_lines = (
        linecov.lineno
        for linecov in filecov.linecov(sort=True)
        if not linecov.has_uncovered_branches
    )

    # Don't do any aggregation on branch results.
    return ",".join(str(lineno) for lineno in covered_lines)


def _uncovered_branches_str(filecov: FileCoverage) -> str:
    uncovered_lines = (
        linecov.lineno
        for linecov in filecov.linecov(sort=True)
        if linecov.has_uncovered_branches
    )

    # Don't do any aggregation on branch results.
    return ",".join(str(lineno) for lineno in uncovered_lines)


def _covered_conditions_str(filecov: FileCoverage) -> str:
    covered_lines = (
        linecov.lineno
        for linecov in filecov.linecov(sort=True)
        if not linecov.has_uncovered_conditions
    )

    # Don't do any aggregation on condition results.
    return ",".join(str(lineno) for lineno in covered_lines)


def _uncovered_conditions_str(filecov: FileCoverage) -> str:
    uncovered_lines = (
        linecov.lineno
        for linecov in filecov.linecov(sort=True)
        if linecov.has_uncovered_conditions
    )

    # Don't do any aggregation on condition results.
    return ",".join(str(lineno) for lineno in uncovered_lines)


def _covered_decisions_str(filecov: FileCoverage) -> str:
    covered_decisions = (
        linecov.lineno
        for linecov in filecov.linecov(sort=True)
        if not linecov.has_uncovered_decisions
    )
    return ",".join(str(lineno) for lineno in covered_decisions)


def _uncovered_decisions_str(filecov: FileCoverage) -> str:
    uncovered_decisions = (
        linecov.lineno
        for linecov in filecov.linecov(sort=True)
        if linecov.has_uncovered_decisions
    )
    return ",".join(str(lineno) for lineno in uncovered_decisions)


def _find_consecutive_ranges(items: Iterable[int]) -> Iterable[tuple[int, int]]:
    first = last = None
    for item in items:
        if last is None:
            first = last = item
            continue

        if item == (last + 1):
            last = item
            continue

        if first is None:
            raise AssertionError("First must not be 'None'")
        yield first, last
        first = last = item

    if last is not None:
        if first is None:
            raise AssertionError("First must not be 'None'")
        yield first, last


def _format_range(first: int, last: int) -> str:
    if first == last:
        return str(first)
    return f"{first}-{last}"
