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

import sys

from .base import Base
from .utils import (
    calculate_coverage,
    get_global_stats,
    open_text_for_writing,
    presentable_filename,
    sort_coverage,
)
from ..configuration import GcovrConfigOption


class Txt(Base):
    def options(self):
        yield GcovrConfigOption(
            "txt",
            ["--txt"],
            group="output_options",
            metavar="OUTPUT",
            help="Generate a text report. "
            "OUTPUT is optional and defaults to --output.",
            nargs="?",
            type=GcovrConfigOption.OutputOrDefault,
            default=None,
            const=GcovrConfigOption.OutputOrDefault(None),
        )
        yield GcovrConfigOption(
            "print_summary",
            ["-s", "--print-summary"],
            group="output_options",
            help="Print a small report to stdout "
            "with line & branch percentage coverage. "
            "This is in addition to other reports. "
            "Default: {default!s}.",
            action="store_true",
        )

    def writers(self, options, logger):
        if options.txt:
            yield (
                [options.txt],
                print_report,
                lambda: logger.warn(
                    "Text output skipped - "
                    "consider providing an output file with `--txt=OUTPUT`."
                ),
            )


def print_report(covdata, output_file, options):
    """produce the classic gcovr text report"""

    with open_text_for_writing(output_file, "coverage.txt") as fh:
        total_lines = 0
        total_covered = 0

        # Header
        fh.write("-" * 78 + "\n")
        fh.write(" " * 27 + "GCC Code Coverage Report\n")
        fh.write("Directory: " + options.root + "\n")

        fh.write("-" * 78 + "\n")
        a = options.show_branch and "Branches" or "Lines"
        b = options.show_branch and "Taken" or "Exec"
        c = "Missing"
        fh.write("File".ljust(40) + a.rjust(8) + b.rjust(8) + "  Cover   " + c + "\n")
        fh.write("-" * 78 + "\n")

        # Data
        keys = sort_coverage(
            covdata,
            show_branch=options.show_branch,
            by_num_uncovered=options.sort_uncovered,
            by_percent_uncovered=options.sort_percent,
        )

        def _summarize_file_coverage(coverage):
            filename = presentable_filename(
                coverage.filename, root_filter=options.root_filter
            )
            filename = filename.ljust(40)
            if len(filename) > 40:
                filename = filename + "\n" + " " * 40

            if options.show_branch:
                total, cover, percent = coverage.branch_coverage()
                uncovered_lines = coverage.uncovered_branches_str()
            else:
                total, cover, percent = coverage.line_coverage()
                uncovered_lines = coverage.uncovered_lines_str()
            percent = "--" if percent is None else str(int(percent))
            return (
                total,
                cover,
                filename
                + str(total).rjust(8)
                + str(cover).rjust(8)
                + percent.rjust(6)
                + "%   "
                + uncovered_lines,
            )

        for key in keys:
            (t, n, txt) = _summarize_file_coverage(covdata[key])
            total_lines += t
            total_covered += n
            fh.write(txt + "\n")

        # Footer & summary
        fh.write("-" * 78 + "\n")
        percent = calculate_coverage(total_covered, total_lines, nan_value=None)
        percent = "--" if percent is None else str(int(percent))
        fh.write(
            "TOTAL".ljust(40)
            + str(total_lines).rjust(8)
            + str(total_covered).rjust(8)
            + str(percent).rjust(6)
            + "%"
            + "\n"
        )
        fh.write("-" * 78 + "\n")


def print_summary_report(covdata):
    """Print a small report to the standard output.
    Output the percentage, covered and total lines and branches.
    """

    (
        lines_total,
        lines_covered,
        percent,
        branches_total,
        branches_covered,
        percent_branches,
    ) = get_global_stats(covdata)

    lines_out = "lines: %0.1f%% (%s out of %s)\n" % (
        percent,
        lines_covered,
        lines_total,
    )
    branches_out = "branches: %0.1f%% (%s out of %s)\n" % (
        percent_branches,
        branches_covered,
        branches_total,
    )

    sys.stdout.write(lines_out)
    sys.stdout.write(branches_out)
