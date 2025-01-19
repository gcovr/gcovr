# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.3
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from typing import Union

from ...coverage import CoverageContainer
from ...formats.base import BaseHandler
from ...options import GcovrConfigOption, OutputOrDefault


class LcovHandler(BaseHandler):
    """Class to handle LCOV format."""

    @classmethod
    def get_options(cls) -> list[Union[GcovrConfigOption, str]]:
        return [
            GcovrConfigOption(
                "lcov",
                ["--lcov"],
                group="output_options",
                metavar="OUTPUT",
                help=(
                    "Generate a LCOV info file. "
                    "OUTPUT is optional and defaults to --output."
                ),
                nargs="?",
                type=OutputOrDefault,
                default=None,
                const=OutputOrDefault(None),
            ),
            GcovrConfigOption(
                "lcov_format_v1",
                ["--lcov-format-1.x"],
                group="output_options",
                help="Write format from LCOV version 1.x instead of 2.x.",
                action="store_true",
            ),
            GcovrConfigOption(
                "lcov_comment",
                ["--lcov-comment"],
                group="output_options",
                metavar="COMMENT",
                help="The comment used in LCOV file.",
            ),
            GcovrConfigOption(
                "lcov_test_name",
                ["--lcov-test-name"],
                group="output_options",
                metavar="NAME",
                help="The name used for TN in LCOV file. Default is '{default!s}'.",
                default="GCOVR report",
            ),
        ]

    def write_report(self, covdata: CoverageContainer, output_file: str) -> None:
        from .write import write_report  # pylint: disable=import-outside-toplevel # Lazy loading is intended here

        write_report(covdata, output_file, self.options)
