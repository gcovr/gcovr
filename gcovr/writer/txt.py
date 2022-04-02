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
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from ..utils import (
    sort_coverage,
    presentable_filename,
    open_text_for_writing,
)
from ..coverage import CovData, CoverageStat, FileCoverage


def print_text_report(covdata: CovData, output_file, options):
    """produce the classic gcovr text report"""

    with open_text_for_writing(output_file, "coverage.txt") as fh:
        # Header
        fh.write("-" * 78 + "\n")
        fh.write(" " * 27 + "GCC Code Coverage Report\n")
        fh.write("Directory: " + options.root + "\n")

        fh.write("-" * 78 + "\n")
        title_total = "Branches" if options.show_branch else "Lines"
        title_covered = "Taken" if options.show_branch else "Exec"
        title_missing = "Missing"
        fh.write(
            "File".ljust(40)
            + title_total.rjust(8)
            + title_covered.rjust(8)
            + "  Cover   "
            + title_missing
            + "\n"
        )
        fh.write("-" * 78 + "\n")

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
        fh.write("-" * 78 + "\n")
        fh.write(_format_line("TOTAL", total_stat, "") + "\n")
        fh.write("-" * 78 + "\n")


def _summarize_file_coverage(coverage: FileCoverage, options):
    filename = presentable_filename(coverage.filename, root_filter=options.root_filter)

    if options.show_branch:
        stat = coverage.branch_coverage()
        uncovered_lines = coverage.uncovered_branches_str()
    else:
        stat = coverage.line_coverage()
        uncovered_lines = coverage.uncovered_lines_str()

    return stat, _format_line(filename, stat, uncovered_lines)


def _format_line(name: str, stat: CoverageStat, uncovered_lines: str) -> str:
    raw_percent = stat.percent
    if raw_percent is None:
        percent = "--"
    else:
        percent = str(int(raw_percent))

    name = name.ljust(40)
    if len(name) > 40:
        name = name + "\n" + " " * 40

    line = (
        name
        + str(stat.total).rjust(8)
        + str(stat.covered).rjust(8)
        + percent.rjust(6)
        + "%"
    )

    if uncovered_lines:
        line += "   " + uncovered_lines

    return line
