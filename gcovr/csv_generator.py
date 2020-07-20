# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import sys
import csv

from .utils import sort_coverage, summarize_file_coverage


def print_csv_report(covdata, output_file, options):
    """produce gcovr csv report"""
    if output_file:
        with open(output_file, 'w') as fh:
            _real_print_csv_report(covdata, fh, options)
    else:
        _real_print_csv_report(covdata, sys.stdout, options)


def _real_print_csv_report(covdata, OUTPUT, options):
    keys = sort_coverage(
        covdata, show_branch=options.show_branch,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent)

    writer = csv.writer(OUTPUT)
    writer.writerow(('filename', 'line_total', 'line_covered', 'line_percent',
                     'branch_total', 'branch_covered', 'branch_percent'))
    for key in keys:
        writer.writerow(summarize_file_coverage(covdata[key],
                                                options.root_filter))
