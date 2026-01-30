# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault


class JaCoCoHandler(BaseHandler):
    """Class to handle JaCoCo format."""

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        return [
            # JSON option use for validation
            "json_compare",
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
            GcovrConfigOption(
                "jacoco_report_name",
                ["--jacoco-report-name"],
                group="output_options",
                metavar="NAME",
                help="The name used for the JaCoCo report. Default is '{default!s}'.",
                default="GCOVR report",
            ),
        ]

    def validate_options(self) -> None:
        """Validate options specific to this format."""
        if self.options.jacoco and self.options.json_compare:
            raise ValueError("A jacoco report is not possible with --json-compare.")

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        from .write import write_report  # pylint: disable=import-outside-toplevel # Lazy loading is intended here

        write_report(covdata, output_file, self.options)
