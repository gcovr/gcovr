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
import logging
import sys

from ..utils import get_global_stats

logger = logging.getLogger("gcovr")


def print_summary(covdata):
    '''Print a small report to the standard output.
    Output the percentage, covered and total lines and branches.
    '''

    (lines_total, lines_covered, percent,
     functions_total, functions_covered, percent_functions,
     branches_total, branches_covered, percent_branches) = get_global_stats(covdata)

    lines_out = "lines: %0.1f%% (%s out of %s)" % (
        percent, lines_covered, lines_total
    )
    functions_out = "functions: %0.1f%% (%s out of %s)" % (
        percent_functions, functions_covered, functions_total
    )
    branches_out = "branches: %0.1f%% (%s out of %s)" % (
        percent_branches, branches_covered, branches_total
    )

    if log_summary:
        logger.info(lines_out)
        logger.info(functions_out)
        logger.info(branches_out)
    else:
        sys.stdout.write(lines_out + '\n')
        sys.stdout.write(functions_out + '\n')
        sys.stdout.write(branches_out + '\n')
