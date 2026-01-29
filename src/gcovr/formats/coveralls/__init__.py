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


class CoverallsHandler(BaseHandler):
    """Class to handle Coveralls format."""

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        return [
            # JSON option use for validation
            "json_compare",
            GcovrConfigOption(
                "coveralls",
                ["--coveralls"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate Coveralls API coverage report in this file name. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "coveralls_pretty",
                ["--coveralls-pretty"],
                group="output_options",
                help=("Pretty-print the coveralls report. Implies --coveralls."),
                action="store_true",
            ),
        ]

    def validate_options(self) -> None:
        """Validate options specific to this format."""
        if self.options.coveralls and self.options.json_compare:
            raise ValueError("A coveralls report is not possible with --json-compare.")

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        from .write import write_report  # pylint: disable=import-outside-toplevel # Lazy loading is intended here

        write_report(covdata, output_file, self.options)
