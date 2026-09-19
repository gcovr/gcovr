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
from ...options import (
    GcovrConfigOption,
    OutputOrDefault,
)


class TxtHandler(BaseHandler):
    """Class to handle text format."""

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        return [
            # Global options needed for report
            "show_calls",
            "show_decision",  # Only for summary report
            # Local options
            GcovrConfigOption(
                "txt_metrics",
                ["--txt-metric"],
                config="txt-metrics",
                group="output_options",
                help=(
                    "The metric type to report. If option is given multiple times the "
                    "reports are printed in the given order. Default is 'line'."
                ),
                choices=("line", "branch", "decision"),
                action="append",
            ),
            GcovrConfigOption(
                "txt_report_covered",
                ["--txt-report-covered"],
                config="txt-covered",
                help="Report the covered lines instead of the uncovered.",
                action="store_true",
            ),
            GcovrConfigOption(
                "txt",
                ["--txt"],
                group="output_options",
                metavar="OUTPUT",
                help="Generate a text report. OUTPUT is optional and defaults to --output.",
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "txt_summary",
                ["-s", "--txt-summary", "--print-summary"],
                group="output_options",
                help=(
                    "Print a small report to stdout "
                    "with line & function & branch percentage coverage "
                    "optional parts are decision & call coverage. "
                    "This is in addition to other reports. "
                ),
                action="store_true",
            ),
        ]

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        from .write import (  # pylint: disable=import-outside-toplevel # Lazy loading is intended here
            write_report,
        )

        write_report(covdata, output_file, self.options)

    def write_summary_report(
        self, covdata: CoverageContainer, output_file: str
    ) -> None:
        from .write import (  # pylint: disable=import-outside-toplevel # Lazy loading is intended here
            write_summary_report,
        )

        write_summary_report(covdata, output_file, self.options)
