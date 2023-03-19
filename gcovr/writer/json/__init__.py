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

import json
import logging
import os
import functools
from typing import Any, Dict, List, Optional

from ...coverage import CovData
from ...utils import force_unix_separator

from ...options import GcovrConfigOption, Options, OutputOrDefault
from ...writer.base import writer_base


LOGGER = logging.getLogger("gcovr")


class writer(writer_base):
    def get_options() -> List[GcovrConfigOption]:
        return [
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
                help="Pretty-print the JSON report. Implies --json. Default: {default!s}.",
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
                help=(
                    "Pretty-print the JSON SUMMARY report."
                    "Implies --json-summary. Default: {default!s}."
                ),
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
        ]

    def print_report(covdata: CovData, output_file: str, options: Options) -> bool:
        from .print import print_report

        return print_report(covdata, output_file, options)

    def print_summary_report(covdata: CovData, output_file: str, options: Options) -> bool:
        from .print import print_summary_report

        return print_summary_report(covdata, output_file, options)
