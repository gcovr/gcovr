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

from ..utils import get_global_stats


def print_summary(covdata):
    '''Print a small report to the standard output.
    Output the percentage, covered and total lines and branches.
    '''

    (lines_total, lines_covered, percent,
     branches_total, branches_covered,
     percent_branches) = get_global_stats(covdata)

    lines_out = "lines: %0.1f%% (%s out of %s)\n" % (
        percent, lines_covered, lines_total
    )
    branches_out = "branches: %0.1f%% (%s out of %s)\n" % (
        percent_branches, branches_covered, branches_total
    )

    sys.stdout.write(lines_out)
    sys.stdout.write(branches_out)
