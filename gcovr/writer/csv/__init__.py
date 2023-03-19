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

import csv
from typing import List, Tuple, Optional

from ...options import GcovrConfigOption, Options, OutputOrDefault
from ...writer.base import writer_base

from ...utils import presentable_filename, open_text_for_writing
from ...coverage import CovData, CoverageStat, SummarizedStats, sort_coverage


class writer(writer_base):
    def get_options() -> List[GcovrConfigOption]:
        return [
            GcovrConfigOption(
                "csv",
                ["--csv"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate a CSV summary report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
        ]

    def print_report(covdata: CovData, output_file: str, options: Options) -> bool:
        from .print import print_report

        return print_report(covdata, output_file, options)
