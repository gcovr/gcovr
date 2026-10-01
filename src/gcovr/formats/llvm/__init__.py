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

"""GCOVR LLVM coverage report input handler."""

import os

from ...data_model.container import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption


class LlvmHandler(BaseHandler):
    """Class to handle LLVM JSON tracefile format."""

    @classmethod
    def get_options(cls) -> list[GcovrConfigOption | str]:
        """Get the report options."""
        return [
            # JSON option use for validation
            "json_compare",
            # Global options needed for processing
            "keep_intermediate_files",
            "delete_input_files",
            # Global options needed for report
            "show_decision",
            # Global options used for merging end exclusion processing.
            "exclude_directory",
            "exclude_noncode_lines",
            "exclude_throw_branches",
            "exclude_unreachable_branches",
            "exclude_function_lines",
            "exclude_internal_functions",
            "respect_exclusion_markers",
            "exclude_function",
            "exclude_lines_by_pattern",
            "exclude_branches_by_pattern",
            "exclude_pattern_prefix",
            "warn_excluded_lines_with_hits",
            "merge_mode_functions",
            # Local options
            GcovrConfigOption(
                "llvm_profdata_cmd",
                ["--llvm-profdata-executable"],
                group="llvm_options",
                help=(
                    "Use a particular llvm-profdata executable to convert LLVM profraw files. "
                    "This switches from searching gcno/gcda files and using gcov to searching "
                    "profraw files (Source-based Code Coverage) of LLVM. "
                    "Must match the compiler you are using, e.g. llvm-profdata-13 for clang-13. "
                    "Defaults to the LLVM_PROFDATA environment variable: '{default!s}'."
                ),
                default=os.environ.get("LLVM_PROFDATA"),
            ),
            GcovrConfigOption(
                "llvm_cov_binaries",
                ["--llvm-cov-binary"],
                group="llvm_options",
                help=(
                    "The binary to export the coverage data for. See help of 'llvm-cov export' command. "
                    "The option can be used multiple times."
                ),
                type=str,
                action="append",
            ),
        ]

    def validate_options(self) -> None:
        """Validate options."""
        if self.options.llvm_profdata_cmd and self.options.json_compare:
            msg = "A LLVM report is not possible with --json-compare."
            raise ValueError(msg)

    def read_report(self) -> CoverageContainer:
        """Read report."""
        # Lazy loading is intended here
        from .read import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            read_report,
        )

        # This can't be checked during validation of arguments because it's not needed together with the
        # tracefiles
        if not self.options.llvm_cov_binaries:
            msg = "Missing --llvm-cov-binary, needed for llvm-cov execution."
            raise RuntimeError(msg)

        return read_report(self.options)
