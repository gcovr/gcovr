# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from typing import Union

from ...coverage import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault


class SonarqubeHandler(BaseHandler):
    """Class to handle Sonarqube format."""

    @classmethod
    def get_options(cls) -> list[Union[GcovrConfigOption, str]]:
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

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        from .write import write_report  # pylint: disable=import-outside-toplevel # Lazy loading is intended here

        write_report(covdata, output_file, self.options)
