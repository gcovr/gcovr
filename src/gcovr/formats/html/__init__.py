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

"""GCOVR HTML report interface."""

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import (
    GcovrConfigOption,
    OutputOrDefault,
    check_input_file,
)

THEMES = (
    "green",
    "blue",
    "boost.blue",
    "boost.green",
    "github.blue",
    "github.green",
    "github.dark-green",
    "github.dark-blue",
)
OPTION_GROUP_NAME = "GCOVR HTML options"
OPTION_GROUP = OPTION_GROUP_NAME.casefold().replace(" ", "_")


class HtmlHandler(BaseHandler):
    """Class to handle HTML format."""

    @classmethod
    def get_option_group(cls) -> dict[str, str]:
        """Get the description of the option group."""
        return {
            "key": OPTION_GROUP,
            "name": OPTION_GROUP_NAME,
            "description": "Options for GCOVR HTML reports with different themes.",
        }

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        """Get the report options."""
        return [
            # Global options needed for report
            "show_calls",
            "show_decision",
            "medium_threshold",
            "high_threshold",
            "medium_threshold_branch",
            "high_threshold_branch",
            "medium_threshold_line",
            "high_threshold_line",
            # Needed for highlighting of GCOVR markers
            "exclude_pattern_prefix",
            # Local options
            GcovrConfigOption(
                "html",
                ["--html"],
                group=OPTION_GROUP,
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
                group=OPTION_GROUP,
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
                group=OPTION_GROUP,
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
                "html_single_page",
                ["--html-single-page"],
                group=OPTION_GROUP,
                help=(
                    "Use one single html output file containing all data in the "
                    "specified mode. If mode is 'js-enabled' (default) and javascript "
                    "is possible the page is interactive like the normal report. "
                    "If mode is 'static' all files are shown at once."
                ),
                action="store_true",
            ),
            GcovrConfigOption(
                "html_static_report",
                ["--html-static-report"],
                group=OPTION_GROUP,
                help="Create a static report without javascript.",
                action="store_true",
            ),
            GcovrConfigOption(
                "html_self_contained",
                ["--html-self-contained"],
                group=OPTION_GROUP,
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
                "html_block_ids",
                ["--html-block-ids"],
                group=OPTION_GROUP,
                help=(
                    "Add the block ids to the HTML report for debugging the branch coverage."
                ),
                action="store_true",
            ),
            GcovrConfigOption(
                "html_template_dir",
                ["--html-template-dir"],
                group=OPTION_GROUP,
                metavar="OUTPUT",
                help=(
                    "Override the default Jinja2 template directory for the HTML report."
                ),
            ),
            GcovrConfigOption(
                "html_syntax_highlighting",
                ["--html-syntax-highlighting", "--html-details-syntax-highlighting"],
                group=OPTION_GROUP,
                help="Use syntax highlighting in HTML source page. Enabled by default.",
                action="store_const",
                default=True,
                const=True,
                const_negate=False,  # autogenerates --no-NAME with action const=False
            ),
            GcovrConfigOption(
                "html_theme",
                ["--html-theme"],
                group=OPTION_GROUP,
                type=str,
                choices=THEMES,
                metavar="THEME",
                help=(
                    "Override the default color theme for the HTML report. "
                    "Default is {default!s}."
                ),
                default=THEMES[0],
            ),
            GcovrConfigOption(
                "html_css",
                ["--html-css"],
                group=OPTION_GROUP,
                type=check_input_file,
                metavar="CSS",
                help="Override the default style sheet for the HTML report.",
                default=None,
            ),
            GcovrConfigOption(
                "html_title",
                ["--html-title"],
                group=OPTION_GROUP,
                metavar="TITLE",
                help="Use TITLE as title for the HTML report. Default is '{default!s}'.",
                default="GCC Code Coverage Report",
            ),
            GcovrConfigOption(
                "html_tab_size",
                ["--html-tab-size"],
                group=OPTION_GROUP,
                help="Used spaces for a tab in a source file. Default is {default!s}",
                type=int,
                default=4,
            ),
            GcovrConfigOption(
                "html_relative_anchors",
                ["--html-absolute-paths"],
                group=OPTION_GROUP,
                help=(
                    "Use absolute paths to link the --html-details reports. "
                    "Defaults to relative links."
                ),
                action="store_false",
            ),
            GcovrConfigOption(
                "html_encoding",
                ["--html-encoding"],
                group=OPTION_GROUP,
                help=(
                    "Override the declared HTML report encoding. "
                    "Defaults to {default!s}. "
                    "See also --source-encoding."
                ),
                default="UTF-8",
            ),
        ]

    def validate_options(self) -> None:
        """Validate options."""
        if self.options.html_title == "":
            msg = "An empty --html-title= is not allowed."
            raise RuntimeError(msg)

        if self.options.html_tab_size < 1:
            msg_0 = "Value of --html-tab-size should be greater 0."
            raise RuntimeError(msg_0)

        if self.options.html_details and self.options.html_nested:
            msg = "--html-details and --html-nested can not be used together."
            raise RuntimeError(msg)

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
            msg = "a named output must be given, if the option --html-details is used."
            raise RuntimeError(msg)

        if self.options.html_nested and not html_output:
            msg = "a named output must be given, if the option --html-nested is used."
            raise RuntimeError(msg)

        if (
            html_output == "-"
            and not self.options.html_single_page
            and (self.options.html_details or self.options.html_nested)
        ):
            msg = (
                "detailed reports can only be printed to STDOUT as --html-single-page."
            )
            raise RuntimeError(msg)

        if self.options.html_single_page and not (
            self.options.html_details or self.options.html_nested
        ):
            msg = "option --html-details or --html-nested is needed, if the option --html-single-page is used."
            raise RuntimeError(msg)

        if self.options.html_self_contained is False and not html_output:
            msg = "can only disable --html-self-contained when a named output is given."
            raise RuntimeError(msg)

        if (
            self.options.html_self_contained is False
            and html_output == "-"
            and not self.options.html_single_page
        ):
            msg = "only self contained reports can be printed to STDOUT"
            raise RuntimeError(msg)

        if self.options.html_theme.startswith("boost") and (
            self.options.html_single_page or self.options.html_static_report
        ):
            msg = "Boost theme is not compatible with --html-single-page or --html-static-report"
            raise RuntimeError(msg)

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        """Write report."""
        # Lazy loading is intended here
        from .write import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            write_report,
        )

        write_report(covdata, output_file, self.options)
