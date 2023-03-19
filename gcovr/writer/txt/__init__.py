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

from ...coverage import CovData

from ...options import GcovrConfigOption, Options, OutputOrDefault
from ...writer.base import writer_base


class writer(writer_base):
    def get_options() -> List[GcovrConfigOption]:
        return [
            GcovrConfigOption(
                "txt",
                ["--txt"],
                group="output_options",
                metavar="OUTPUT",
                help="Generate a text report. OUTPUT is optional and defaults to --output.",
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "print_summary",
                ["-s", "--print-summary"],
                group="output_options",
                help=(
                    "Print a small report to stdout "
                    "with line & function & branch percentage coverage. "
                    "This is in addition to other reports. "
                    "Default: {default!s}."
                ),
                action="store_true",
            ),
        ]

    def print_report(covdata: CovData, output_file: str, options: Options) -> bool:
        from .print import print_report

        return print_report(covdata, output_file, options)

    def print_summary_report(covdata: CovData, output_file: str, options: Options) -> bool:
        from .print import print_summary_report

        return print_summary_report(covdata, output_file, options)
