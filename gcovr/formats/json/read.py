# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0+master, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import json
import logging
import os
from glob import glob
from typing import Optional

from ...options import Options


from ..gcov.read import apply_filter_include_exclude
from ...coverage import (
    BranchCoverage,
    CovData,
    DecisionCoverage,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
    CallCoverage,
)
from ...merging import (
    get_merge_mode_from_options,
    insert_branch_coverage,
    insert_decision_coverage,
    insert_file_coverage,
    insert_function_coverage,
    insert_line_coverage,
    insert_call_coverage,
)

from . import versions

LOGGER = logging.getLogger("gcovr")


#
#  Get coverage from already existing gcovr JSON files
#
def read_report(options: Options) -> CovData:
    """merge a coverage from multiple reports in the format
    partially compatible with gcov JSON output"""

    if len(options.json_add_tracefile) == 0:
        return None

    datafiles = set()

    for trace_files_regex in options.json_add_tracefile:
        trace_files = glob(trace_files_regex, recursive=True)
        if not trace_files:
            raise RuntimeError(
                "Bad --add-tracefile option.\n" "\tThe specified file does not exist."
            )
        else:
            for trace_file in trace_files:
                datafiles.add(os.path.normpath(trace_file))

    covdata = dict()
    for filename in datafiles:
        LOGGER.debug(f"Processing JSON file: {filename}")

        with open(filename, "r") as json_file:
            gcovr_json_data = json.load(json_file)

        version = str(gcovr_json_data["gcovr/format_version"])
        assert (
            version == versions.JSON_FORMAT_VERSION
        ), "Wrong format version, got {} expected {}.".format(
            version, versions.JSON_FORMAT_VERSION
        )

        for gcovr_file in gcovr_json_data["files"]:
            file_path = os.path.join(
                os.path.abspath(options.root), os.path.normpath(gcovr_file["file"])
            )

            filtered, excluded = apply_filter_include_exclude(
                file_path, options.filter, options.exclude
            )

            # Ignore if the filename does not match the filter
            if filtered:
                LOGGER.debug(f"  Filtering coverage data for file {file_path}")
                continue

            # Ignore if the filename matches the exclude pattern
            if excluded:
                LOGGER.debug(f"  Excluding coverage data for file {file_path}")
                continue

            file_coverage = FileCoverage(file_path)
            merge_options = get_merge_mode_from_options(options)
            for json_function in gcovr_file["functions"]:
                insert_function_coverage(
                    file_coverage, _function_from_json(json_function), merge_options
                )
            for json_line in gcovr_file["lines"]:
                insert_line_coverage(file_coverage, _line_from_json(json_line))

            insert_file_coverage(covdata, file_coverage, merge_options)

    return covdata


def _function_from_json(json_function: dict) -> FunctionCoverage:
    return FunctionCoverage(
        name=json_function["name"],
        lineno=json_function["lineno"],
        count=json_function["execution_count"],
        excluded=json_function.get("gcovr/excluded", False),
    )


def _line_from_json(json_line: dict) -> LineCoverage:
    line = LineCoverage(
        json_line["line_number"],
        count=json_line["count"],
        excluded=json_line.get("gcovr/excluded", False),
        md5=json_line.get("gcovr/md5", None),
    )

    for branchno, json_branch in enumerate(json_line["branches"]):
        insert_branch_coverage(line, branchno, _branch_from_json(json_branch))

    insert_decision_coverage(line, _decision_from_json(json_line.get("gcovr/decision")))

    if "gcovr/calls" in json_line:
        for json_call in json_line["gcovr/calls"]:
            insert_call_coverage(line, _call_from_json(json_call))

    return line


def _branch_from_json(json_branch: dict) -> BranchCoverage:
    return BranchCoverage(
        blockno=json_branch["blockno"],
        count=json_branch["count"],
        fallthrough=json_branch["fallthrough"],
        throw=json_branch["throw"],
    )


def _call_from_json(json_call: dict) -> CallCoverage:
    return CallCoverage(covered=json_call["covered"], callno=json_call["callno"])


def _decision_from_json(json_decision: Optional[dict]) -> Optional[DecisionCoverage]:
    if json_decision is None:
        return None

    decision_type = json_decision["type"]

    if decision_type == "uncheckable":
        return DecisionCoverageUncheckable()

    if decision_type == "conditional":
        return DecisionCoverageConditional(
            json_decision["count_true"], json_decision["count_false"]
        )
    if decision_type == "switch":
        return DecisionCoverageSwitch(json_decision["count"])

    raise RuntimeError(f"Unknown decision type: {decision_type!r}")
