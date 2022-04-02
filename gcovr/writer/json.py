# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.1, a parsing and reporting tool for gcov.
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
from typing import Any, Dict

from ..gcov import apply_filter_include_exclude
from ..utils import (
    presentable_filename,
    sort_coverage,
    open_text_for_writing,
)
from ..coverage import (
    CovData,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    FileCoverage,
    SummarizedStats,
)
from ..merging import merge_covdata

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


#
# Produce gcovr JSON report
#
def print_json_report(covdata: CovData, output_file, options):
    r"""produce an JSON report in the format partially
    compatible with gcov JSON output"""

    gcovr_json_root = {}
    gcovr_json_root["gcovr/format_version"] = JSON_FORMAT_VERSION
    gcovr_json_root["files"] = []

    for no in sorted(covdata):
        gcovr_json_file = {}
        gcovr_json_file["file"] = presentable_filename(
            covdata[no].filename, root_filter=options.root_filter
        )
        gcovr_json_file["lines"] = _json_from_lines(covdata[no].lines)
        gcovr_json_file["functions"] = _json_from_functions(covdata[no].functions)
        gcovr_json_root["files"].append(gcovr_json_file)

    _write_json_result(
        gcovr_json_root, output_file, "coverage.json", options.json_pretty
    )


#
# Produce gcovr JSON summary report
#
def print_json_summary_report(covdata, output_file, options):

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
            _functions_from_json(file_coverage, gcovr_file["functions"])
            _lines_from_json(file_coverage, gcovr_file["lines"])

            covdata = merge_covdata(covdata, {file_path: file_coverage})

    return covdata


def _json_from_lines(lines):
    json_lines = [_json_from_line(lines[no]) for no in sorted(lines)]
    return json_lines


def _json_from_line(line):
    json_line = {}
    json_line["branches"] = _json_from_branches(line.branches)
    if line.decision is not None:
        json_line["gcovr/decision"] = _json_from_decision(line.decision)
    json_line["count"] = line.count
    json_line["line_number"] = line.lineno
    json_line["gcovr/noncode"] = line.noncode
    json_line["gcovr/excluded"] = line.excluded
    return json_line


def _json_from_branches(branches):
    json_branches = [_json_from_branch(branches[no]) for no in sorted(branches)]
    return json_branches


def _json_from_branch(branch):
    json_branch = {}
    json_branch["count"] = branch.count
    json_branch["fallthrough"] = branch.fallthrough
    json_branch["throw"] = branch.throw
    return json_branch


def _json_from_decision(decision):
    json_decision = {}
    if decision.is_uncheckable:
        json_decision["type"] = "uncheckable"
    elif decision.is_conditional:
        json_decision["type"] = "conditional"
        json_decision["count_true"] = decision.count_true
        json_decision["count_false"] = decision.count_false
    elif decision.is_switch:
        json_decision["type"] = "switch"
        json_decision["count"] = decision.count
    else:
        RuntimeError("Unknown decision type")

    return json_decision


def _json_from_functions(functions):
    json_functions = [
        _json_from_function(functions[name]) for name in sorted(functions)
    ]
    return json_functions


def _json_from_function(function):
    json_function = {}
    if function:
        json_function["lineno"] = function.lineno
        json_function["name"] = function.name
        json_function["execution_count"] = function.count
    return json_function


def _functions_from_json(file, json_functions):
    [
        _function_from_json(file.function(json_function["name"]), json_function)
        for json_function in json_functions
    ]


def _function_from_json(function, json_function):
    function.count = json_function["execution_count"]
    function.lineno = json_function["lineno"]


def _lines_from_json(file, json_lines):
    [
        _line_from_json(file.line(json_line["line_number"]), json_line)
        for json_line in json_lines
    ]


def _line_from_json(line, json_line):
    line.noncode = json_line["gcovr/noncode"]
    line.excluded = json_line["gcovr/excluded"]
    line.count = json_line["count"]
    _branches_from_json(line, json_line["branches"])
    if "gcovr/decision" in json_line:
        _decision_from_json(line, json_line["gcovr/decision"])


def _branches_from_json(line, json_branches):
    [
        _branch_from_json(line.branch(no), json_branch)
        for no, json_branch in enumerate(json_branches, 0)
    ]


def _branch_from_json(branch, json_branch):
    branch.fallthrough = json_branch["fallthrough"]
    branch.throw = json_branch["throw"]
    branch.count = json_branch["count"]


def _decision_from_json(line, json_decision):
    line.decision = None
    if json_decision["type"] == "uncheckable":
        line.decision = DecisionCoverageUncheckable()
    elif json_decision["type"] == "conditional":
        line.decision = DecisionCoverageConditional(
            json_decision["count_true"], json_decision["count_false"]
        )
    elif json_decision["type"] == "switch":
        line.decision = DecisionCoverageSwitch(json_decision["count"])
    else:
        RuntimeError("Unknown decision type")
