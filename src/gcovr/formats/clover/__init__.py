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

"""GCOVR clover report interface."""

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault


class CloverHandler(BaseHandler):
    """Class to handle Clover format."""

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        """Get the report options."""
        return [
            # JSON option use for validation
            "json_compare",
            # Global options used for merging.
            "merge_mode_functions",
            # Local options
            GcovrConfigOption(
                "clover",
                ["--clover"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate a Clover XML report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "clover_pretty",
                ["--clover-pretty"],
                group="output_options",
                help=("Pretty-print the Clover XML report. Implies --clover."),
                action="store_true",
            ),
            GcovrConfigOption(
                "clover_project",
                ["--clover-project"],
                group="output_options",
                type=str,
                help=("The project name for the Clover XML report."),
            ),
        ]

    def validate_options(self) -> None:
        """Validate options."""
        if self.options.clover and self.options.json_compare:
            msg = "A clover report is not possible with --json-compare."
            raise ValueError(msg)

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        """Write report."""
        # Lazy loading is intended here
        from .write import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            write_report,
        )

        write_report(covdata, output_file, self.options)
