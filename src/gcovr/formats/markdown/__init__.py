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

import logging
from typing import Union

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault, check_percentage

LOGGER = logging.getLogger("gcovr")
THEMES = (
    "green",
    "blue",
)


class MarkdownHandler(BaseHandler):
    """Class to handle markdown format."""

    @classmethod
    def get_options(cls) -> list[Union[GcovrConfigOption, str]]:
        return [
            # Global options needed for report
            "exclude_calls",
            "show_decision",  # Only for summary report
            # Local options
            GcovrConfigOption(
                "markdown",
                ["--markdown"],
                group="output_options",
                metavar="OUTPUT",
                help="Generate a markdown report. OUTPUT is optional and defaults to --output.",
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "markdown_summary",
                ["--markdown-summary"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate a markdown summary report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "markdown_theme",
                ["--markdown-theme"],
                group="output_options",
                type=str,
                choices=THEMES,
                metavar="THEME",
                help=(
                    "Override the default color theme for the Markdown report. "
                    "Default is {default!s}."
                ),
                default=THEMES[0],
            ),
            GcovrConfigOption(
                "md_medium_threshold",
                ["--markdown-medium-threshold"],
                group="output_options",
                type=check_percentage,
                metavar="MEDIUM",
                help=(
                    "If the coverage is below MEDIUM, the value is marked "
                    "as low coverage in the markdown report. "
                    "MEDIUM has to be lower than or equal to value of --md-high-threshold "
                    "and greater than 0. "
                    "If MEDIUM is equal to value of --markdown-high-threshold the report has "
                    "only high and low coverage. Default is {default!s}."
                ),
                default=75.0,
            ),
            GcovrConfigOption(
                "md_high_threshold",
                ["--markdown-high-threshold"],
                group="output_options",
                type=check_percentage,
                metavar="HIGH",
                help=(
                    "If the coverage is below HIGH, the value is marked "
                    "as medium coverage in the markdown report. "
                    "HIGH has to be greater than or equal to value of --markdown-medium-threshold. "
                    "If HIGH is equal to value of --markdown-medium-threshold the report has "
                    "only high and low coverage. Default is {default!s}."
                ),
                default=90.0,
            ),
        ]

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        from .write import write_report  # pylint: disable=import-outside-toplevel # Lazy loading is intended here

        write_report(covdata, output_file, self.options)

    def write_summary_report(
        self, covdata: CoverageContainer, output_file: str
    ) -> None:
        from .write import write_summary_report  # pylint: disable=import-outside-toplevel # Lazy loading is intended here

        write_summary_report(covdata, output_file, self.options)
