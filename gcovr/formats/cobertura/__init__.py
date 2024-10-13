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

from typing import List

from ...options import GcovrConfigOption, OutputOrDefault
from ...formats.base import BaseHandler

from ...coverage import CovData


class CoberturaHandler(BaseHandler):
    @classmethod
    def get_options(cls) -> List[GcovrConfigOption]:
        return [
            # Global options used for merging.
            "merge_mode_functions",
            # Local options
            GcovrConfigOption(
                "cobertura",
                ["--cobertura", "-x", "--xml"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate a Cobertura XML report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "cobertura_pretty",
                ["--cobertura-pretty", "--xml-pretty"],
                group="output_options",
                help=("Pretty-print the Cobertura XML report. Implies --cobertura."),
                action="store_true",
            ),
            GcovrConfigOption(
                "cobertura_add_tracefile",
                ["--cobertura-add-tracefile"],
                config="cobertura-add-tracefile",
                help=(
                    "Combine the coverage data from Cobertura XML files. "
                    "When this option is used gcov is not run to collect "
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
