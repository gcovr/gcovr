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

import logging
from typing import List

from ...coverage import CovData

from ...options import (
    GcovrConfigOption,
    GcovrDeprecatedConfigOptionAction,
    OutputOrDefault,
)
from ...formats.base import BaseHandler

LOGGER = logging.getLogger("gcovr")


class UseBranchMetricAction(GcovrDeprecatedConfigOptionAction):
    option = "--txt-metric"
    config = "txt-metric"
    value = "branch"


class TxtHandler(BaseHandler):
    @classmethod
    def get_options(cls) -> List[GcovrConfigOption]:
        return [
            # Global options needed for report
            "exclude_calls",
            "show_decision",  # Only for summary report
            # Local options
            GcovrConfigOption(
                "txt_metric",
                ["--txt-metric"],
                config="txt-metric",
                group="output_options",
                help=("The metric type to report."),
                choices=["line", "branch", "decision"],
                default="line",
            ),
            GcovrConfigOption(
                "txt_metric",
                ["-b", "--txt-branches", "--branches"],
                config="txt-branch",
                group="output_options",
                help=(
                    "Deprecated, please use '--txt-metric branch' instead."
                    "Report the branch coverage instead of the line coverage in text report."
                ),
                nargs=0,
                action=UseBranchMetricAction,
            ),
            GcovrConfigOption(
                "txt_report_covered",
                ["--txt-report-covered"],
                config="txt-covered",
                help="Report the covered lines instead of the uncovered.",
                action="store_true",
            ),
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
                "txt_summary",
                ["-s", "--txt-summary", "--print-summary"],
                group="output_options",
                help=(
                    "Print a small report to stdout "
                    "with line & function & branch percentage coverage "
                    "optional parts are decision & call coverage. "
                    "This is in addition to other reports. "
                ),
                action="store_true",
            ),
        ]

    def write_report(self, covdata: CovData, output_file: str) -> None:
        from .write import write_report

        write_report(covdata, output_file, self.options)

    def write_summary_report(self, covdata: CovData, output_file: str) -> None:
        from .write import write_summary_report

        write_summary_report(covdata, output_file, self.options)
