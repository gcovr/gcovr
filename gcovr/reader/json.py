# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 4.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import json
import os
import sys

from glob import glob

from .base import Base
from ..gcov import apply_filter_include_exclude
from ..coverage import FileCoverage
from ..configuration import GcovrConfigOption
from ..writer.json import JSON_FORMAT_VERSION


class Json(Base):
    def options(self):
        yield GcovrConfigOption(
            "add_tracefile",
            ["-a", "--add-tracefile"],
            help="Combine the coverage data from JSON files. "
            "Coverage files contains source files structure relative "
            "to root directory. Those structures are combined "
            "in the output relative to the current root directory. "
            "Unix style wildcards can be used to add the pathnames "
            "matching a specified pattern. In this case pattern "
            "must be set in double quotation marks. "
            "Option can be specified multiple times. "
            "When option is used gcov is not run to collect "
            "the new coverage data.",
            action="append",
            default=[],
        )

    def read(self, covdata, options, logger):
        r"""merge a coverage from multiple reports in the format
        partially compatible with gcov JSON output"""

        if len(options.add_tracefile):
            filenames = set()
            for trace_files_regex in options.add_tracefile:
                trace_files = glob(trace_files_regex, recursive=True)
                if not trace_files:
                    logger.error(
                        "Bad --add-tracefile option.\n"
                        "\tThe specified file does not exist."
                    )
                    sys.exit(1)
                else:
                    for trace_file in trace_files:
                        filenames.add(os.path.normpath(trace_file))

            for filename in filenames:
                gcovr_json_data = {}
                logger.verbose_msg("Processing JSON file: {}", filename)

                with open(filename, "r") as json_file:
                    gcovr_json_data = json.load(json_file)

                version = str(gcovr_json_data["gcovr/format_version"])
                assert (
                    version == JSON_FORMAT_VERSION
                ), "Wrong format version, got {} expected {}.".format(
                    version, JSON_FORMAT_VERSION
                )

                coverage = {}
                for gcovr_file in gcovr_json_data["files"]:
                    file_path = os.path.join(
                        os.path.abspath(options.root),
                        os.path.normpath(gcovr_file["file"]),
                    )

                    filtered, excluded = apply_filter_include_exclude(
                        file_path, options.filter, options.exclude
                    )

                    # Ignore if the filename does not match the filter
                    if filtered:
                        logger.verbose_msg(
                            "  Filtering coverage data for file {}", file_path
                        )
                        continue

                    # Ignore if the filename matches the exclude pattern
                    if excluded:
                        logger.verbose_msg(
                            "  Excluding coverage data for file {}", file_path
                        )
                        continue

                    file_coverage = FileCoverage(file_path)
                    self._lines_from_json(file_coverage, gcovr_file["lines"])
                    coverage[file_path] = file_coverage

                self._split_coverage_results(covdata, coverage)

    def _split_coverage_results(self, covdata, coverages):
        for coverage in coverages.values():
            if coverage.filename not in covdata:
                covdata[coverage.filename] = FileCoverage(coverage.filename)

            covdata[coverage.filename].update(coverage)

    def _lines_from_json(self, file, json_lines):
        [
            self._line_from_json(file.line(json_line["line_number"]), json_line)
            for json_line in json_lines
        ]

    def _line_from_json(self, line, json_line):
        line.noncode = json_line["gcovr/noncode"]
        line.count = json_line["count"]
        self._branches_from_json(line, json_line["branches"])

    def _branches_from_json(self, line, json_branches):
        [
            self._branch_from_json(line.branch(no), json_branch)
            for no, json_branch in enumerate(json_branches, 0)
        ]

    def _branch_from_json(self, branch, json_branch):
        branch.fallthrough = json_branch["fallthrough"]
        branch.throw = json_branch["throw"]
        branch.count = json_branch["count"]
