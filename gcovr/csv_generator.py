# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import csv

from .utils import sort_coverage, summarize_file_coverage, open_text_for_writing, fixup_percent


def print_csv_report(covdata, output_file, options):
    """produce gcovr csv report"""

    with open_text_for_writing(output_file, 'coverage.csv') as fh:
        keys = sort_coverage(
            covdata, show_branch=options.show_branch,
            by_num_uncovered=options.sort_uncovered,
            by_percent_uncovered=options.sort_percent)

        writer = csv.writer(fh)
        writer.writerow(('filename', 'line_total', 'line_covered', 'line_percent',
                        'branch_total', 'branch_covered', 'branch_percent'))
        for key in keys:
            summary = summarize_file_coverage(covdata[key], options.root_filter)
            writer.writerow((summary['filename'], summary['line_total'], summary['line_covered'],
                             fixup_percent(summary['line_percent']),
                             summary['branch_total'], summary['branch_covered'],
                             fixup_percent(summary['branch_covered_percent'])))
