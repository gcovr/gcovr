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

"""GCOVR SonarQube report interface."""

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault

OPTION_GROUP_NAME = "SonarQube XML options"
OPTION_GROUP = OPTION_GROUP_NAME.casefold().replace(" ", "_")


class SonarqubeHandler(BaseHandler):
    """Class to handle Sonarqube format."""

    @classmethod
    def get_option_group(cls) -> dict[str, str]:
        """Get the description of the option group."""
        return {
            "key": OPTION_GROUP,
            "name": OPTION_GROUP_NAME,
            "description": (
                "Options for report generation in SonarQube generic format, see "
                "<https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/test-coverage/generic-test-data>."
            ),
        }

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        """Get the report options."""
        return [
            # JSON option use for validation
            "json_compare",
            # Global options needed for report
            "show_decision",
            GcovrConfigOption(
                "sonarqube",
                ["--sonarqube"],
                group=OPTION_GROUP,
                metavar="OUTPUT",
                help=(
                    "Generate Sonarqube generic coverage report in this file name. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "sonarqube_pretty",
                ["--sonarqube-pretty"],
                group=OPTION_GROUP,
                help=("Pretty-print the Sonarqube XML report. Implies --sonarqube."),
                action="store_true",
            ),
            GcovrConfigOption(
                "sonarqube_metric",
                ["--sonarqube-metric"],
                config="sonarqube-metric",
                group=OPTION_GROUP,
                help=("The metric type to report. Default is '{default!s}'."),
                choices=("line", "branch", "condition", "decision"),
                default="branch",
            ),
        ]

    def validate_options(self) -> None:
        """Validate options."""
        if self.options.sonarqube and self.options.json_compare:
            msg = "A sonarqube report is not possible with --json-compare."
            raise ValueError(msg)

        if (
            self.options.sonarqube_metric == "decision"
            and not self.options.show_decision
        ):
            msg = "--sonarqube-metric=decision needs the option --decisions."
            raise RuntimeError(msg)

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        """Write report."""
        # Lazy loading is intended here
        from .write import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            write_report,
        )

        write_report(covdata, output_file, self.options)
