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

"""GCOVR Cobertura report interface."""

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault

OPTION_GROUP_NAME = "Cobertura XML options"
OPTION_GROUP = OPTION_GROUP_NAME.casefold().replace(" ", "_")


class CoberturaHandler(BaseHandler):
    """Class to handle Cobertura format."""

    @classmethod
    def get_option_group(cls) -> dict[str, str]:
        """Get the description of the option group."""
        return {
            "key": OPTION_GROUP,
            "name": OPTION_GROUP_NAME,
            "description": (
                "Options for report generation in Cobertura format, "
                "see <https://github.com/cobertura/cobertura>. "
                "The XML file follows the schema "
                "<https://github.com/cobertura/cobertura/blob/e5eea8679ebce047ec6ccdfdbf6cf2c14b376875/cobertura/src/site/htdocs/xml/coverage-04.dtd>."
                "Reports in Cobertura format can also be used as input for GCOVR."
            ),
        }

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
                "cobertura",
                ["--cobertura", "-x", "--xml"],
                group=OPTION_GROUP,
                metavar="OUTPUT",
                help=(
                    "Generate a Cobertura XML report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "cobertura_pretty",
                ["--cobertura-pretty", "--xml-pretty"],
                group=OPTION_GROUP,
                help=("Pretty-print the Cobertura XML report. Implies --cobertura."),
                action="store_true",
            ),
            GcovrConfigOption(
                "cobertura_tracefile",
                ["--cobertura-add-tracefile"],
                config="cobertura-add-tracefile",
                group=OPTION_GROUP,
                help=(
                    "Combine the coverage data from Cobertura XML files. "
                    "When this option is used gcov is not run to collect "
                    "the new coverage data."
                ),
                action="append",
                default=[],
            ),
        ]

    def validate_options(self) -> None:
        """Validate options."""
        if self.options.json_compare:
            if self.options.cobertura:
                msg = "A cobertura report is not possible with --json-compare."
                raise ValueError(msg)

            if self.options.cobertura_tracefile:
                msg = "A cobertura tracefile is not possible with --json-compare."
                raise ValueError(msg)

    def read_report(self) -> CoverageContainer:
        """Read report."""
        from .read import (  # pylint: disable=import-outside-toplevel # Lazy loading is intended here  # noqa: PLC0415
            read_report,
        )

        return read_report(self.options)

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        """Write report."""
        # Lazy loading is intended here
        from .write import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            write_report,
        )

        write_report(covdata, output_file, self.options)
