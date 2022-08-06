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

import sys

from ..coverage import CovData, CoverageStat, SummarizedStats


def print_summary(covdata: CovData):
    """Print a small report to the standard output.
    Output the percentage, covered and total lines and branches.
    """

    def print_stat(name: str, stat: CoverageStat):
        percent = stat.percent_or(0.0)
        covered = stat.covered
        total = stat.total
        sys.stdout.write(f"{name}: {percent:0.1f}% ({covered} out of {total})\n")

    stats = SummarizedStats.from_covdata(covdata)

    print_stat("lines", stats.line)
    print_stat("functions", stats.function)
    print_stat("branches", stats.branch)
    sys.stdout.flush()
