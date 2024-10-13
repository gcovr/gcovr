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

from multiprocessing import cpu_count
import os
from typing import List

from ...options import GcovrConfigOption, relative_path
from ...formats.base import BaseHandler

from ...coverage import CovData

from ...utils import FilterOption


class GcovHandler(BaseHandler):
    @classmethod
    def get_options(cls) -> List[GcovrConfigOption]:
        return [
            # Global options needed for report
            "show_decision",
            # Global options used for merging end exclusion processing.
            "exclude_calls",
            "exclude_noncode_lines",
            "exclude_throw_branches",
            "exclude_unreachable_branches",
            "exclude_function_lines",
            "exclude_internal_functions",
            "respect_exclusion_markers",
            "exclude_functions",
            "exclude_lines_by_pattern",
            "exclude_branches_by_pattern",
            "exclude_pattern_prefix",
            "merge_mode_functions",
            # Local options
            GcovrConfigOption(
                "gcov_files",
                ["-g", "--gcov-use-existing-files", "--use-gcov-files"],
                group="gcov_options",
                help="Use existing gcov files for analysis.",
                action="store_true",
            ),
            GcovrConfigOption(
                "gcov_ignore_errors",
                ["--gcov-ignore-errors"],
                group="gcov_options",
                choices=[
                    "all",
                    "source_not_found",
                    "output_error",
                    "no_working_dir_found",
                ],
                nargs="?",
                const="all",
                default=None,
                help=(
                    "Ignore errors from invoking GCOV command "
                    "instead of exiting with an error. "
                    "A report will be shown on stderr. "
                    "Default is '{default!s}'."
                ),
                type=str,
                action="append",
            ),
            GcovrConfigOption(
                "gcov_ignore_parse_errors",
                ["--gcov-ignore-parse-errors"],
                group="gcov_options",
                choices=[
                    "all",
                    "negative_hits.warn",
                    "negative_hits.warn_once_per_file",
                    "suspicious_hits.warn",
                    "suspicious_hits.warn_once_per_file",
                ],
                nargs="?",
                const="all",
                default=None,
                help=(
                    "Skip lines with parse errors in GCOV files "
                    "instead of exiting with an error. "
                    "A report will be shown on stderr. "
                    "Default is '{default!s}'."
                ),
                type=str,
                action="append",
            ),
            GcovrConfigOption(
                "gcov_filter",
                ["--gcov-filter"],
                group="filter_options",
                help=(
                    "Keep only gcov data files that match this filter. "
                    "Can be specified multiple times."
                ),
                action="append",
                type=FilterOption,
                default=[],
            ),
            GcovrConfigOption(
                "gcov_exclude",
                ["--gcov-exclude"],
                group="filter_options",
                help=(
                    "Exclude gcov data files that match this filter. "
                    "Can be specified multiple times."
                ),
                action="append",
                type=FilterOption,
                default=[],
            ),
            GcovrConfigOption(
                "gcov_exclude_dirs",
                ["--gcov-exclude-directories", "--exclude-directories"],
                group="filter_options",
                help=(
                    "Exclude directories that match this regex "
                    "while searching raw coverage files. "
                    "Can be specified multiple times."
                ),
                action="append",
                type=FilterOption.NonEmpty,
                default=[],
            ),
            GcovrConfigOption(
                "gcov_cmd",
                ["--gcov-executable"],
                group="gcov_options",
                help=(
                    "Use a particular gcov executable. "
                    "Must match the compiler you are using, "
                    "e.g. 'llvm-cov gcov' for Clang. "
                    "Can include additional arguments. "
                    "Defaults to the GCOV environment variable, "
                    "or 'gcov': '{default!s}'."
                ),
                default=os.environ.get("GCOV", "gcov"),
            ),
            GcovrConfigOption(
                "gcov_objdir",
                ["--gcov-object-directory", "--object-directory"],
                group="gcov_options",
                help=(
                    "Override normal working directory detection. "
                    "Gcovr needs to identify the path between gcda files "
                    "and the directory where the compiler was originally run. "
                    "Normally, gcovr can guess correctly. "
                    "This option specifies either "
                    "the path from gcc to the gcda file (i.e. gcc's '-o' option), "
                    "or the path from the gcda file to gcc's working directory."
                ),
                type=relative_path,
            ),
            GcovrConfigOption(
                "gcov_keep",
                ["-k", "--gcov-keep", "--keep"],
                config="keep-gcov-files",
                group="gcov_options",
                help=(
                    "Keep gcov files after processing. "
                    "This applies both to files that were generated by gcovr, "
                    "or were supplied via the --gcov-use-existing-files option. "
                ),
                action="store_true",
            ),
            GcovrConfigOption(
                "gcov_delete",
                ["-d", "--gcov-delete", "--delete"],
                config="delete-gcov-files",
                group="gcov_options",
                help="Delete gcda files after processing.",
                action="store_true",
            ),
            GcovrConfigOption(
                "gcov_parallel",
                ["-j"],
                config="gcov-parallel",
                group="gcov_options",
                help="Set the number of threads to use in parallel.",
                nargs="?",
                const=cpu_count(),
                type=int,
                default=1,
            ),
        ]

    def validate_options(self) -> None:
        if self.options.gcov_objdir is not None and not os.path.exists(
            self.options.gcov_objdir
        ):
            raise RuntimeError(
                "Bad --gcov-object-directory option.\n"
                "\tThe specified directory does not exist."
            )

    def read_report(self) -> CovData:
        from .read import read_report

        return read_report(self.options)
