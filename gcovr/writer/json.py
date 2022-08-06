# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2022 the gcovr authors
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
import functools
import re
from typing import Any, Dict, Optional

from ..gcov import apply_filter_include_exclude
from ..utils import (
    presentable_filename,
    sort_coverage,
    open_text_for_writing,
)
from ..coverage import (
    BranchCoverage,
    CovData,
    DecisionCoverage,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
    SummarizedStats,
)
from ..merging import (
    insert_branch_coverage,
    insert_decision_coverage,
    insert_file_coverage,
    insert_function_coverage,
    insert_line_coverage,
)

logger = logging.getLogger("gcovr")


JSON_FORMAT_VERSION = "0.3"
JSON_SUMMARY_FORMAT_VERSION = "0.5"
PRETTY_JSON_INDENT = 4


def _write_json_result(gcovr_json_dict, output_file, default_filename, pretty):
    r"""helper utility to output json format dictionary to a file/STDOUT"""
    write_json = json.dump

    if pretty:
        write_json = functools.partial(
            write_json,
            indent=PRETTY_JSON_INDENT,
            separators=(",", ": "),
            sort_keys=True,
        )
    else:
        write_json = functools.partial(write_json, sort_keys=True)

    with open_text_for_writing(output_file, default_filename) as fh:
        write_json(gcovr_json_dict, fh)


def print_json_report(covdata: CovData, output_file, options):
    r"""produce an JSON report in the format partially
    compatible with gcov JSON output"""

    gcovr_json_root = {
        "gcovr/format_version": JSON_FORMAT_VERSION,
        "files": _json_from_files(covdata, options.root_filter),
    }

    _write_json_result(
        gcovr_json_root, output_file, "coverage.json", options.json_pretty
    )


def print_json_summary_report(covdata, output_file, options):
    """Produce gcovr JSON summary report"""

    json_dict = {}

    json_dict["root"] = os.path.relpath(
        options.root,
        os.getcwd() if output_file == "-" else os.path.dirname(output_file),
    )
    json_dict["gcovr/summary_format_version"] = JSON_SUMMARY_FORMAT_VERSION
    json_dict["files"] = []

    # Data
    keys = sort_coverage(
        covdata,
        show_branch=options.show_branch,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent,
    )

    for key in keys:
        filename = presentable_filename(covdata[key].filename, options.root_filter)

        json_dict["files"].append(
            {
                "filename": filename,
                **_summary_from_stats(SummarizedStats.from_file(covdata[key]), None),
            }
        )

    # Footer & summary
    json_dict.update(_summary_from_stats(SummarizedStats.from_covdata(covdata), 0.0))

    _write_json_result(
        json_dict, output_file, "summary_coverage.json", options.json_summary_pretty
    )


def _summary_from_stats(stats: SummarizedStats, default) -> Dict[str, Any]:
    json_dict: Dict[str, Any] = dict()

    json_dict["line_total"] = stats.line.total
    json_dict["line_covered"] = stats.line.covered
    json_dict["line_percent"] = stats.line.percent_or(default)

    json_dict["function_total"] = stats.function.total
    json_dict["function_covered"] = stats.function.covered
    json_dict["function_percent"] = stats.function.percent_or(default)

    json_dict["branch_total"] = stats.branch.total
    json_dict["branch_covered"] = stats.branch.covered
    json_dict["branch_percent"] = stats.branch.percent_or(default)

    return json_dict


#
#  Get coverage from already existing gcovr JSON files
#
def gcovr_json_files_to_coverage(filenames, options) -> CovData:
    r"""merge a coverage from multiple reports in the format
    partially compatible with gcov JSON output"""

    covdata: CovData = dict()
    for filename in filenames:
        logger.debug(f"Processing JSON file: {filename}")

        with open(filename, "r") as json_file:
            gcovr_json_data = json.load(json_file)

        version = str(gcovr_json_data["gcovr/format_version"])
        assert (
            version == JSON_FORMAT_VERSION
        ), "Wrong format version, got {} expected {}.".format(
            version, JSON_FORMAT_VERSION
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
                logger.debug(f"  Filtering coverage data for file {file_path}")
                continue

            # Ignore if the filename matches the exclude pattern
            if excluded:
                logger.debug(f"  Excluding coverage data for file {file_path}")
                continue

            file_coverage = FileCoverage(file_path)
            for json_function in gcovr_file["functions"]:
                insert_function_coverage(
                    file_coverage, _function_from_json(json_function)
                )
            for json_line in gcovr_file["lines"]:
                insert_line_coverage(file_coverage, _line_from_json(json_line))

            insert_file_coverage(covdata, file_coverage)

    return covdata


def _json_from_files(files: CovData, root_filter: re.Pattern) -> list:
    return [_json_from_file(files[key], root_filter) for key in sorted(files)]


def _json_from_file(file: FileCoverage, root_filter: re.Pattern) -> dict:
    return {
        "file": presentable_filename(file.filename, root_filter),
        "lines": _json_from_lines(file.lines),
        "functions": _json_from_functions(file.functions),
    }


def _json_from_lines(lines: Dict[int, LineCoverage]) -> list:
    return [_json_from_line(lines[no]) for no in sorted(lines)]


def _json_from_line(line: LineCoverage) -> dict:
    json_line = {
        "line_number": line.lineno,
        "count": line.count,
        "branches": _json_from_branches(line.branches),
        "gcovr/noncode": line.noncode,
        "gcovr/excluded": line.excluded,
    }
    if line.decision is not None:
        json_line["gcovr/decision"] = _json_from_decision(line.decision)
    return json_line


def _json_from_branches(branches: Dict[int, BranchCoverage]) -> list:
    return [_json_from_branch(branches[no]) for no in sorted(branches)]


def _json_from_branch(branch: BranchCoverage) -> dict:
    return {
        "count": branch.count,
        "fallthrough": branch.fallthrough,
        "throw": branch.throw,
    }


def _json_from_decision(decision: DecisionCoverage) -> dict:
    if isinstance(decision, DecisionCoverageUncheckable):
        return {"type": "uncheckable"}

    if isinstance(decision, DecisionCoverageConditional):
        return {
            "type": "conditional",
            "count_true": decision.count_true,
            "count_false": decision.count_false,
        }

    if isinstance(decision, DecisionCoverageSwitch):
        return {
            "type": "switch",
            "count": decision.count,
        }

    raise RuntimeError("Unknown decision type: {decision!r}")


def _json_from_functions(functions: Dict[str, FunctionCoverage]) -> list:
    return [_json_from_function(functions[name]) for name in sorted(functions)]


def _json_from_function(function: FunctionCoverage) -> dict:
    return {
        "name": function.name,
        "lineno": function.lineno,
        "execution_count": function.count,
    }


def _function_from_json(json_function: dict) -> FunctionCoverage:
    return FunctionCoverage(
        name=json_function["name"],
        lineno=json_function["lineno"],
        call_count=json_function["execution_count"],
    )


def _line_from_json(json_line: dict) -> LineCoverage:
    line = LineCoverage(
        json_line["line_number"],
        count=json_line["count"],
        noncode=json_line["gcovr/noncode"],
        excluded=json_line["gcovr/excluded"],
    )

    for branchno, json_branch in enumerate(json_line["branches"]):
        insert_branch_coverage(line, branchno, _branch_from_json(json_branch))

    insert_decision_coverage(line, _decision_from_json(json_line.get("gcovr/decision")))

    return line


def _branch_from_json(json_branch: dict) -> BranchCoverage:
    return BranchCoverage(
        count=json_branch["count"],
        fallthrough=json_branch["fallthrough"],
        throw=json_branch["throw"],
    )


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
