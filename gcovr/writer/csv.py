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

import csv

from ..utils import sort_coverage, summarize_file_coverage, open_text_for_writing


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
            writer.writerow(summarize_file_coverage(covdata[key],
                                                    options.root_filter))
