# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.2
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

import csv
from typing import Tuple, Optional

from ...options import Options

from ...utils import presentable_filename, open_text_for_writing
from ...coverage import CovData, CoverageStat, SummarizedStats, sort_coverage


def write_report(covdata: CovData, output_file: str, options: Options) -> None:
    """produce gcovr csv report"""

    # Open output without translation of line endings.
    # The CSV writer uses as default line endings "\r\n" (according to
    # https://datatracker.ietf.org/doc/html/rfc4180)
    with open_text_for_writing(output_file, "coverage.csv", newline="") as fh:
        keys = sort_coverage(
            covdata,
            sort_key=options.sort_key,
            sort_reverse=options.sort_reverse,
            by_metric="branch" if options.sort_branches else "line",
        )

        writer = csv.writer(fh)
        writer.writerow(
            (
                "filename",
                "line_total",
                "line_covered",
                "line_percent",
                "branch_total",
                "branch_covered",
                "branch_percent",
                "function_total",
                "function_covered",
                "function_percent",
            )
        )
        for key in keys:
            filename = presentable_filename(covdata[key].filename, options.root_filter)
            stats = SummarizedStats.from_file(covdata[key])
            writer.writerow(
                [
                    filename,
                    *_stat_tuple(stats.line),
                    *_stat_tuple(stats.branch),
                    *_stat_tuple(stats.function),
                ]
            )


def _stat_tuple(stat: CoverageStat) -> Tuple[int, int, Optional[float]]:
    """creates tuple (total, covered, ratio) with ratio in range 0..1 incl"""
    percent = stat.percent
    if percent is not None:
        percent = percent / 100.0
    return stat.total, stat.covered, percent
