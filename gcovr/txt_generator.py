# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import sys

from .utils import calculate_coverage


#
# Produce the classic gcovr text report
#
def print_text_report(covdata, options):
    def _num_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        return total - covered

    def _percent_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        if covered:
            return -1.0 * covered / total
        else:
            return total or 1e6

    def _alpha(key):
        return key

    if options.output:
        OUTPUT = open(options.output, 'w')
    else:
        OUTPUT = sys.stdout
    total_lines = 0
    total_covered = 0

    # Header
    OUTPUT.write("-" * 78 + '\n')
    OUTPUT.write(" " * 27 + "GCC Code Coverage Report\n")
    OUTPUT.write("Directory: " + options.root + "\n")

    OUTPUT.write("-" * 78 + '\n')
    a = options.show_branch and "Branches" or "Lines"
    b = options.show_branch and "Taken" or "Exec"
    c = "Missing"
    OUTPUT.write(
        "File".ljust(40) + a.rjust(8) + b.rjust(8) + "  Cover   " + c + "\n"
    )
    OUTPUT.write("-" * 78 + '\n')

    # Data
    keys = list(covdata.keys())
    keys.sort(
        key=options.sort_uncovered and _num_uncovered or
        options.sort_percent and _percent_uncovered or _alpha
    )

    def _summarize_file_coverage(coverage):
        tmp = options.root_filter.sub('', coverage.fname)
        if not coverage.fname.endswith(tmp):
            # Do no truncation if the filter does not start matching at
            # the beginning of the string
            tmp = coverage.fname
        tmp = tmp.replace('\\', '/').ljust(40)
        if len(tmp) > 40:
            tmp = tmp + "\n" + " " * 40

        (total, cover, percent) = coverage.coverage(options.show_branch)
        uncovered_lines = coverage.uncovered_str(
            exceptional=False, show_branch=options.show_branch)
        if not options.show_branch:
            t = coverage.uncovered_str(
                exceptional=True, show_branch=options.show_branch)
            if len(t):
                uncovered_lines += " [* " + t + "]"
        return (total, cover,
                tmp + str(total).rjust(8) + str(cover).rjust(8) +
                percent.rjust(6) + "%   " + uncovered_lines)

    for key in keys:
        (t, n, txt) = _summarize_file_coverage(covdata[key])
        total_lines += t
        total_covered += n
        OUTPUT.write(txt + '\n')

    # Footer & summary
    OUTPUT.write("-" * 78 + '\n')
    percent = calculate_coverage(total_covered, total_lines, nan_value=None)
    percent = "--" if percent is None else str(int(percent))
    OUTPUT.write(
        "TOTAL".ljust(40) + str(total_lines).rjust(8) +
        str(total_covered).rjust(8) + str(percent).rjust(6) + "%" + '\n'
    )
    OUTPUT.write("-" * 78 + '\n')

    # Close logfile
    if options.output:
        OUTPUT.close()
