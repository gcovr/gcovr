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

from typing import List, Union

from ...coverage import CovData
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault


class JaCoCoHandler(BaseHandler):
    """Class to handle JaCoCo format."""

    @classmethod
    def get_options(cls) -> List[Union[GcovrConfigOption, str]]:
        return [
            GcovrConfigOption(
                "jacoco",
                ["--jacoco"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate a JaCoCo XML report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "jacoco_pretty",
                ["--jacoco-pretty"],
                group="output_options",
                help=("Pretty-print the JaCoCo XML report. Implies --jacoco."),
                action="store_true",
            ),
        ]

    def write_report(self, covdata: CovData, output_file: str) -> None:
        from .write import write_report  # pylint: disable=import-outside-toplevel # Lazy loading is intended here

        write_report(covdata, output_file, self.options)
