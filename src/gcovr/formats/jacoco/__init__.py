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

"""GCOVR JaCoCo report interface."""

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault

OPTION_GROUP_NAME = "JaCoCo XML options"
OPTION_GROUP = OPTION_GROUP_NAME.casefold().replace(" ", "_")


class JaCoCoHandler(BaseHandler):
    """Class to handle JaCoCo format."""

    @classmethod
    def get_option_group(cls) -> dict[str, str]:
        """Get the description of the option group."""
        return {
            "key": OPTION_GROUP,
            "name": OPTION_GROUP_NAME,
            "description": (
                "Options for report generation in JaCoCo format, "
                "see <https://github.com/jacoco/jacoco>. "
                "The XML file follows the schema "
                "<https://www.jacoco.org/jacoco/trunk/coverage/report.dtd>."
            ),
        }

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        """Get the report options."""
        return [
            # JSON option use for validation
            "json_compare",
            GcovrConfigOption(
                "jacoco",
                ["--jacoco"],
                group=OPTION_GROUP,
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
                group=OPTION_GROUP,
                help=("Pretty-print the JaCoCo XML report. Implies --jacoco."),
                action="store_true",
            ),
            GcovrConfigOption(
                "jacoco_report_name",
                ["--jacoco-report-name"],
                group=OPTION_GROUP,
                metavar="NAME",
                help="The name used for the JaCoCo report. Default is '{default!s}'.",
                default="GCOVR report",
            ),
        ]

    def validate_options(self) -> None:
        """Validate options."""
        if self.options.jacoco and self.options.json_compare:
            msg = "A JaCoCo report is not possible with --json-compare."
            raise RuntimeError(msg)

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        """Write report."""
        # Lazy loading is intended here
        from .write import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            write_report,
        )

        write_report(covdata, output_file, self.options)
