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
import os
from typing import List

from ...options import GcovrConfigOption, OutputOrDefault
from ...formats.base import BaseHandler

from ...coverage import CovData
from ...utils import force_unix_separator

LOGGER = logging.getLogger("gcovr")


class JsonHandler(BaseHandler):
    @classmethod
    def get_options(cls) -> List[GcovrConfigOption]:
        return [
            # Global options used for merging.
            "merge_mode_functions",
            "show_decision",
            # Local options
            GcovrConfigOption(
                "json",
                ["--json"],
                group="output_options",
                metavar="OUTPUT",
                help="Generate a JSON report. OUTPUT is optional and defaults to --output.",
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "json_pretty",
                ["--json-pretty"],
                group="output_options",
                help="Pretty-print the JSON report. Implies --json.",
                action="store_true",
            ),
            GcovrConfigOption(
                "json_summary",
                ["--json-summary"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate a JSON summary report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "json_summary_pretty",
                ["--json-summary-pretty"],
                group="output_options",
                help="Pretty-print the JSON SUMMARY report. Implies --json-summary.",
                action="store_true",
            ),
            GcovrConfigOption(
                "json_base",
                ["--json-base"],
                group="output_options",
                metavar="PATH",
                help="Prepend the given path to all file paths in JSON report.",
                type=lambda p: force_unix_separator(os.path.normpath(p)),
                default=None,
            ),
            GcovrConfigOption(
                "json_add_tracefile",
                ["-a", "--json-add-tracefile", "--add-tracefile"],
                config="add-tracefile",
                help=(
                    "Combine the coverage data from JSON files. "
                    "Coverage files contains source files structure relative "
                    "to root directory. Those structures are combined "
                    "in the output relative to the current root directory. "
                    "Unix style wildcards can be used to add the pathnames "
                    "matching a specified pattern. In this case pattern "
                    "must be set in double quotation marks. "
                    "Option can be specified multiple times. "
                    "When option is used gcov is not run to collect "
                    "the new coverage data."
                ),
                action="append",
                default=[],
            ),
        ]

    def read_report(self) -> CovData:
        from .read import read_report

        return read_report(self.options)

    def write_report(self, covdata: CovData, output_file: str) -> None:
        from .write import write_report

        write_report(covdata, output_file, self.options)

    def write_summary_report(self, covdata: CovData, output_file: str) -> None:
        from .write import write_summary_report

        write_summary_report(covdata, output_file, self.options)
