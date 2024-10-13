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
from typing import List

from ...options import (
    GcovrConfigOption,
    OutputOrDefault,
    check_input_file,
    check_percentage,
)
from ...formats.base import BaseHandler

from ...coverage import CovData

LOGGER = logging.getLogger("gcovr")


class HtmlHandler(BaseHandler):
    @classmethod
    def get_options(cls) -> List[GcovrConfigOption]:
        from .write import CssRenderer

        return [
            # Global options needed for report
            "exclude_calls",
            "show_decision",
            # Local options
            GcovrConfigOption(
                "html",
                ["--html"],
                group="output_options",
                metavar="OUTPUT",
                help="Generate a HTML report. OUTPUT is optional and defaults to --output.",
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "html_details",
                ["--html-details"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Add annotated source code reports to the HTML report. "
                    "Implies --html, can not be used together with --html-nested. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "html_nested",
                ["--html-nested"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Add annotated source code reports to the HTML report. "
                    "A page is created for each directory that summarize subdirectories "
                    "with aggregated statistics. "
                    "Implies --html, can not be used together with --html-details. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "html_template_dir",
                ["--html-template-dir"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Override the default Jinja2 template directory for the HTML report. "
                ),
            ),
            GcovrConfigOption(
                "html_syntax_highlighting",
                ["--html-syntax-highlighting", "--html-details-syntax-highlighting"],
                group="output_options",
                help="Use syntax highlighting in HTML source page. Enabled by default.",
                action="store_const",
                default=True,
                const=True,
                const_negate=False,  # autogenerates --no-NAME with action const=False
            ),
            GcovrConfigOption(
                "html_theme",
                ["--html-theme"],
                group="output_options",
                type=str,
                choices=CssRenderer.get_themes(),
                metavar="THEME",
                help=(
                    "Override the default color theme for the HTML report. "
                    "Default is {default!s}."
                ),
                default=CssRenderer.get_default_theme(),
            ),
            GcovrConfigOption(
                "html_css",
                ["--html-css"],
                group="output_options",
                type=check_input_file,
                metavar="CSS",
                help="Override the default style sheet for the HTML report.",
                default=None,
            ),
            GcovrConfigOption(
                "html_title",
                ["--html-title"],
                group="output_options",
                metavar="TITLE",
                help="Use TITLE as title for the HTML report. Default is '{default!s}'.",
                default="GCC Code Coverage Report",
            ),
            GcovrConfigOption(
                "html_medium_threshold",
                ["--html-medium-threshold"],
                group="output_options",
                type=check_percentage,
                metavar="MEDIUM",
                help=(
                    "If the coverage is below MEDIUM, the value is marked "
                    "as low coverage in the HTML report. "
                    "MEDIUM has to be lower than or equal to value of --html-high-threshold "
                    "and greater than 0. "
                    "If MEDIUM is equal to value of --html-high-threshold the report has "
                    "only high and low coverage. Default is {default!s}."
                ),
                default=75.0,
            ),
            GcovrConfigOption(
                "html_high_threshold",
                ["--html-high-threshold"],
                group="output_options",
                type=check_percentage,
                metavar="HIGH",
                help=(
                    "If the coverage is below HIGH, the value is marked "
                    "as medium coverage in the HTML report. "
                    "HIGH has to be greater than or equal to value of --html-medium-threshold. "
                    "If HIGH is equal to value of --html-medium-threshold the report has "
                    "only high and low coverage. Default is {default!s}."
                ),
                default=90.0,
            ),
            GcovrConfigOption(
                "html_medium_threshold_branch",
                ["--html-medium-threshold-branch"],
                group="output_options",
                metavar="MEDIUM_BRANCH",
                type=check_percentage,
                help="If the coverage is below MEDIUM_BRANCH, the value is marked "
                "as low coverage in the HTML report. "
                "MEDIUM_BRANCH has to be lower than or equal to value of --html-high-threshold-branch "
                "and greater than 0. "
                "If MEDIUM_BRANCH is equal to value of --html-medium-threshold-branch the report has "
                "only high and low coverage. Default is taken from --html-medium-threshold.",
                default=None,
            ),
            GcovrConfigOption(
                "html_high_threshold_branch",
                ["--html-high-threshold-branch"],
                group="output_options",
                type=check_percentage,
                metavar="HIGH_BRANCH",
                help="If the coverage is below HIGH_BRANCH, the value is marked "
                "as medium coverage in the HTML report. "
                "HIGH_BRANCH has to be greater than or equal to value of --html-medium-threshold-branch. "
                "If HIGH_BRANCH is equal to value of --html-medium-threshold-branch the report has "
                "only high and low coverage. Default is taken from --html-high-threshold.",
                default=None,
            ),
            GcovrConfigOption(
                "html_medium_threshold_line",
                ["--html-medium-threshold-line"],
                group="output_options",
                metavar="MEDIUM_LINE",
                type=check_percentage,
                help="If the coverage is below MEDIUM_LINE, the value is marked "
                "as low coverage in the HTML report. "
                "MEDIUM_LINE has to be lower than or equal to value of --html-high-threshold-line "
                "and greater than 0. "
                "If MEDIUM_LINE is equal to value of --html-medium-threshold-line the report has "
                "only high and low coverage. Default is taken from --html-medium-threshold.",
                default=None,
            ),
            GcovrConfigOption(
                "html_high_threshold_line",
                ["--html-high-threshold-line"],
                group="output_options",
                type=check_percentage,
                metavar="HIGH_LINE",
                help="If the coverage is below HIGH_LINE, the value is marked "
                "as medium coverage in the HTML report. "
                "HIGH_LINE has to be greater than or equal to value of --html-medium-threshold-line. "
                "If HIGH_LINE is equal to value of --html-medium-threshold-line the report has "
                "only high and low coverage. Default is taken from --html-high-threshold.",
                default=None,
            ),
            GcovrConfigOption(
                "html_tab_size",
                ["--html-tab-size"],
                group="output_options",
                help="Used spaces for a tab in a source file. Default is {default!s}",
                type=int,
                default=4,
            ),
            GcovrConfigOption(
                "html_relative_anchors",
                ["--html-absolute-paths"],
                group="output_options",
                help=(
                    "Use absolute paths to link the --html-details reports. "
                    "Defaults to relative links."
                ),
                action="store_false",
            ),
            GcovrConfigOption(
                "html_encoding",
                ["--html-encoding"],
                group="output_options",
                help=(
                    "Override the declared HTML report encoding. "
                    "Defaults to {default!s}. "
                    "See also --source-encoding."
                ),
                default="UTF-8",
            ),
            GcovrConfigOption(
                "html_self_contained",
                ["--html-self-contained"],
                group="output_options",
                help=(
                    "Control whether the HTML report bundles resources like CSS styles. "
                    "Self-contained reports can be sent via email, "
                    "but conflict with the Content Security Policy of some web servers. "
                    "Defaults to self-contained reports unless --html-details or "
                    "--html-nested is used without --html-single-page."
                ),
                action="store_const",
                default=None,
                const=True,
                const_negate=False,
            ),
            GcovrConfigOption(
                "html_single_page",
                ["--html-single-page"],
                group="output_options",
                choices=["static", "js-enabled"],
                nargs="?",
                const="js-enabled",
                default=None,
                help=(
                    "Use one single html output file containing all data in the "
                    "specified mode. If mode is 'js-enabled' (default) and javascript "
                    "is possible the page is interactive like the normal report. "
                    "If mode is 'static' all files are shown at once."
                ),
            ),
        ]

    def validate_options(self) -> None:
        if self.options.html_tab_size < 1:
            raise RuntimeError("value of --html-tab-size= should be greater 0.")

        if self.options.html_details and self.options.html_nested:
            raise RuntimeError(
                "--html-details and --html-nested can not be used together."
            )

        html_output = None
        if self.options.html and self.options.html.value:
            html_output = self.options.html.value
        elif self.options.html_details and self.options.html_details.value:
            html_output = self.options.html_details.value
        elif self.options.html_nested and self.options.html_nested.value:
            html_output = self.options.html_nested.value
        elif self.options.output and self.options.output.value:
            html_output = self.options.output.value

        if self.options.html_details and not html_output:
            raise RuntimeError(
                "a named output must be given, if the option --html-details is used."
            )

        if self.options.html_nested and not html_output:
            raise RuntimeError(
                "a named output must be given, if the option --html-nested is used."
            )

        if (
            html_output == "-"
            and not self.options.html_single_page
            and (self.options.html_details or self.options.html_nested)
        ):
            raise RuntimeError(
                "detailed reports can only be printed to STDOUT as --html-single-page."
            )

        if self.options.html_single_page and not (
            self.options.html_details or self.options.html_nested
        ):
            raise RuntimeError(
                "option --html-details or --html-nested is needed, if the option --html-single-page is used."
            )

        if self.options.html_self_contained is False and not html_output:
            raise RuntimeError(
                "can only disable --html-self-contained when a named output is given."
            )

        if (
            self.options.html_self_contained is False
            and html_output == "-"
            and not self.options.html_single_page
        ):
            raise RuntimeError("only self contained reports can be printed to STDOUT")

    def write_report(self, covdata: CovData, output_file: str) -> None:
        from .write import write_report

        write_report(covdata, output_file, self.options)
