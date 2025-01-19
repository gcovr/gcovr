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

import json
import logging
import os
from glob import glob
from typing import Any, Optional

from . import versions
from ...coverage import (
    BranchCoverage,
    ConditionCoverage,
    CoverageContainer,
    DecisionCoverage,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
    CallCoverage,
)
from ...filter import is_file_excluded
from ...merging import (
    get_merge_mode_from_options,
    insert_branch_coverage,
    insert_condition_coverage,
    insert_decision_coverage,
    insert_file_coverage,
    insert_function_coverage,
    insert_line_coverage,
    insert_call_coverage,
)
from ...options import Options

LOGGER = logging.getLogger("gcovr")


#
#  Get coverage from already existing gcovr JSON files
#
def read_report(options: Options) -> CoverageContainer:
    """merge a coverage from multiple reports in the format
    partially compatible with gcov JSON output"""

    covdata = CoverageContainer()
    if len(options.json_add_tracefile) == 0:
        return covdata

    datafiles = set()

    for trace_files_regex in options.json_add_tracefile:
        trace_files = glob(trace_files_regex, recursive=True)
        if not trace_files:
            raise RuntimeError(
                "Bad --json-add-tracefile option.\n"
                "\tThe specified file does not exist."
            )

        for trace_file in trace_files:
            datafiles.add(os.path.normpath(trace_file))

    for data_source_filename in datafiles:
        LOGGER.debug(f"Processing JSON file: {data_source_filename}")

        with open(data_source_filename, encoding="utf-8") as json_file:
            gcovr_json_data = json.load(json_file)

        version = str(gcovr_json_data["gcovr/format_version"])
        if version != versions.JSON_FORMAT_VERSION:
            raise AssertionError(
                f"Wrong format version, got {version} expected {versions.JSON_FORMAT_VERSION}."
            )

        for gcovr_file in gcovr_json_data["files"]:
            file_path = os.path.join(
                os.path.abspath(options.root), os.path.normpath(gcovr_file["file"])
            )

            if is_file_excluded(file_path, options.filter, options.exclude):
                continue

            filecov = FileCoverage(
                file_path, gcovr_file.get("gcovr/data_sources", data_source_filename)
            )
            merge_options = get_merge_mode_from_options(options)
            for json_function in gcovr_file["functions"]:
                insert_function_coverage(
                    filecov, _function_from_json(json_function), merge_options
                )
            for json_line in gcovr_file["lines"]:
                insert_line_coverage(filecov, _line_from_json(json_line))

            insert_file_coverage(covdata, filecov, merge_options)

    return covdata


def _function_from_json(json_function: dict[str, Any]) -> FunctionCoverage:
    start: Optional[tuple[int, int]] = None
    end: Optional[tuple[int, int]] = None
    if "pos" in json_function:
        start_l_c = json_function["pos"][0].split(":", maxsplit=1)
        start = (int(start_l_c[0]), int(start_l_c[1]))
        end_l_c = json_function["pos"][1].split(":", maxsplit=1)
        end = (int(end_l_c[0]), int(end_l_c[1]))
    return FunctionCoverage(
        json_function.get("name"),
        json_function["demangled_name"],
        lineno=json_function["lineno"],
        count=json_function["execution_count"],
        blocks=json_function["blocks_percent"],
        start=start,
        end=end,
        excluded=json_function.get("gcovr/excluded", False),
    )


def _line_from_json(json_line: dict[str, Any]) -> LineCoverage:
    linecov = LineCoverage(
        json_line["line_number"],
        count=json_line["count"],
        function_name=json_line.get("function_name"),
        block_ids=json_line.get("block_ids"),
        md5=json_line.get("gcovr/md5"),
        excluded=json_line.get("gcovr/excluded", False),
    )

    for branchno, json_branch in enumerate(json_line["branches"]):
        insert_branch_coverage(linecov, branchno, _branch_from_json(json_branch))

    if "conditions" in json_line:
        for conditionno, json_branch in enumerate(json_line["conditions"]):
            insert_condition_coverage(
                linecov, conditionno, _condition_from_json(json_branch)
            )

    insert_decision_coverage(
        linecov, _decision_from_json(json_line.get("gcovr/decision"))
    )

    if "gcovr/calls" in json_line:
        for json_call in json_line["gcovr/calls"]:
            insert_call_coverage(linecov, _call_from_json(json_call))

    return linecov


def _branch_from_json(json_branch: dict[str, Any]) -> BranchCoverage:
    return BranchCoverage(
        source_block_id=json_branch["source_block_id"],
        count=json_branch["count"],
        fallthrough=json_branch["fallthrough"],
        throw=json_branch["throw"],
        destination_block_id=json_branch.get("destination_block_id"),
        excluded=json_branch.get("gcovr/excluded"),
    )


def _condition_from_json(json_condition: dict[str, Any]) -> ConditionCoverage:
    return ConditionCoverage(
        count=json_condition["count"],
        covered=json_condition["covered"],
        not_covered_false=json_condition["not_covered_false"],
        not_covered_true=json_condition["not_covered_true"],
    )


def _call_from_json(json_call: dict[str, Any]) -> CallCoverage:
    return CallCoverage(callno=json_call["callno"], covered=json_call["covered"])


def _decision_from_json(
    json_decision: Optional[dict[str, Any]],
) -> Optional[DecisionCoverage]:
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

    raise AssertionError(f"Unknown decision type: {decision_type!r}")
