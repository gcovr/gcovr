# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
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

from typing import List

from ...options import GcovrConfigOption, OutputOrDefault
from ...formats.base import BaseHandler

from ...coverage import CovData


class CloverHandler(BaseHandler):
    """Class to handle Clover format."""

    @classmethod
    def get_options(cls) -> List[GcovrConfigOption]:
        return [
            # Global options used for merging.
            "merge_mode_functions",
            "merge_mode_conditions",
            # Local options
            GcovrConfigOption(
                "clover",
                ["--clover"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate a Clover XML report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "clover_pretty",
                ["--clover-pretty"],
                group="output_options",
                help=("Pretty-print the Clover XML report. Implies --clover."),
                action="store_true",
            ),
            GcovrConfigOption(
                "clover_project",
                ["--clover-project"],
                group="output_options",
                type=str,
                help=("The project name for the Clover XML report."),
            ),
        ]

    def write_report(self, covdata: CovData, output_file: str) -> None:
        from .write import write_report  # pylint: disable=import-outside-toplevel # Lazy loading is intended here

        write_report(covdata, output_file, self.options)
