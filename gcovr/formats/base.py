# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0+master, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from typing import List

from ..options import GcovrConfigOption, Options
from ..coverage import CovData


class handler_base(object):
    def get_options() -> List[GcovrConfigOption]:
        return []

    @staticmethod
    def read_report(covdata: CovData, options: Options) -> bool:
        raise RuntimeError("Function 'read_report' not implemented.")

    @staticmethod
    def write_report(covdata: CovData, output_file: str, options: Options) -> bool:
        raise RuntimeError("Function 'write_report' not implemented.")

    @staticmethod
    def write_summary_report(
        covdata: CovData, output_file: str, options: Options
    ) -> bool:
        raise RuntimeError("Function 'write_summary_report' not implemented.")
