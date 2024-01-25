# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 7.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
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


class SonarqubeHandler(BaseHandler):
    def get_options() -> List[GcovrConfigOption]:
        return [
            GcovrConfigOption(
                "sonarqube",
                ["--sonarqube"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate sonarqube generic coverage report in this file name. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
        ]

    def write_report(self, covdata: CovData, output_file: str) -> None:
        from .write import write_report

        write_report(covdata, output_file, self.options)
