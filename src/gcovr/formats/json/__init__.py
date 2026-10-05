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

"""GCOVR JSON report interface."""

import os

from gcovr.logging import LOGGER

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault
from ...utils import force_unix_separator

OPTION_GROUP_NAME = "GCOVR JSON options"
OPTION_GROUP = OPTION_GROUP_NAME.casefold().replace(" ", "_")


class JsonHandler(BaseHandler):
    """Class to handle own JSON tracefile format."""

    @classmethod
    def get_option_group(cls) -> dict[str, str]:
        """Get the description of the option group."""
        return {
            "key": OPTION_GROUP,
            "name": OPTION_GROUP_NAME,
            "description": (
                "Options for report generation in GCOVR JSON intermediate format. "
                "This file format contains a dump of the internal data model and "
                "can be used as input file to write other reports."
            ),
        }

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        """Get the report options."""
        return [
            # Global options used for output
            "verbose",
            # Global options used for merging.
            "merge_mode_functions",
            "show_decision",
            # Local options
            GcovrConfigOption(
                "json",
                ["--json"],
                group=OPTION_GROUP,
                metavar="OUTPUT",
                help="Generate a JSON report. OUTPUT is optional and defaults to --output.",
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "json_pretty",
                ["--json-pretty"],
                group=OPTION_GROUP,
                help="Pretty-print the JSON report. Implies --json.",
                action="store_true",
            ),
            GcovrConfigOption(
                "json_summary",
                ["--json-summary"],
                group=OPTION_GROUP,
                metavar="OUTPUT",
                help=(
                    "Generate a JSON summary report. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "json_summary_pretty",
                ["--json-summary-pretty"],
                group=OPTION_GROUP,
                help="Pretty-print the JSON SUMMARY report. Implies --json-summary.",
                action="store_true",
            ),
            GcovrConfigOption(
                "json_base",
                ["--json-base"],
                group=OPTION_GROUP,
                metavar="PATH",
                help="Prepend the given path to all file paths in JSON report.",
                type=lambda p: force_unix_separator(os.path.normpath(p)),
                default=None,
            ),
            GcovrConfigOption(
                "json_tracefile",
                ["-a", "--json-add-tracefile", "--add-tracefile"],
                group=OPTION_GROUP,
                config="add-tracefile",
                help=(
                    "Combine the coverage data from JSON files. "
                    "Coverage files contains source files structure relative "
                    "to root directory. Those structures are combined "
                    "in the output relative to the current root directory. "
                    "Unix style wildcards can be used to add the pathnames "
                    "matching a specified pattern. In this case pattern "
                    "must be set in double quotation marks. "
                    "Option can be specified multiple times. "
                    "When option is used gcov is not executed to collect "
                    "the new coverage data. "
                    "ATTENTION: The option --merge-lines doesn't affect the "
                    "JSON files and needs to be added when the JSON files are "
                    "processed to generate the reports."
                ),
                action="append",
                default=[],
            ),
            GcovrConfigOption(
                "json_trace_data_source",
                ["--json-trace-data-source"],
                group=OPTION_GROUP,
                help="Write the data source to the tracefile.",
                action="store_true",
            ),
            GcovrConfigOption(
                "json_compare",
                ["--json-compare"],
                group=OPTION_GROUP,
                help=(
                    "Compare exactly two JSON files given with --json-add-tracefile. "
                    "The comparison result is available for text, JSON and HTML report."
                ),
                action="store_true",
            ),
        ]

    def validate_options(self) -> None:
        """Validate options."""
        if self.options.json_compare and len(self.options.json_tracefile) != 2:  # noqa: PLR2004
            msg = (
                "--json-compare requires exactly two input trace files "
                f"but {len(self.options.json_tracefile)} were given."
            )
            raise ValueError(msg)

        if self.options.json_tracefile:
            for option, key in [
                ("--exclude-directory", "exclude_directory"),
                ("--exclude-noncode-lines", "exclude_noncode_lines"),
                ("--exclude-throw-branches", "exclude_throw_branches"),
                ("--exclude-unreachable-branches", "exclude_unreachable_branches"),
                ("--exclude-function-lines", "exclude_function_lines"),
                ("--exclude-function", "exclude_function"),
                ("--exclude-lines-by-pattern", "exclude_lines_by_pattern"),
                ("--exclude-branches-by-pattern", "exclude_branches_by_pattern"),
                ("--warn-excluded-lines-with-hits", "warn_excluded_lines_with_hits"),
            ]:
                if self.all_options_for_validation.get(key):
                    LOGGER.warning(
                        "Option %s has no effect when generating reports from tracefiles.",
                        option,
                    )
            for option, key in [
                ("--include-internal-functions", "exclude_internal_functions"),
                ("--no-markers", "respect_exclusion_markers"),
            ]:
                if not self.all_options_for_validation.get(key):
                    LOGGER.warning(
                        "Option %s has no effect when generating reports from tracefiles.",
                        option,
                    )

    def read_report(self) -> CoverageContainer:
        """Read report."""
        # Lazy loading is intended here
        from .read import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
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

    def write_summary_report(
        self, covdata: CoverageContainer, output_file: str
    ) -> None:
        """Write summary report."""
        # Lazy loading is intended here
        from .write import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            write_summary_report,
        )

        write_summary_report(covdata, output_file, self.options)
