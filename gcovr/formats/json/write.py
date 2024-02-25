# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 7.2+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
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

import json
import logging
import os
import functools
from typing import Any, Dict

from ...options import Options

from ...utils import (
    presentable_filename,
    open_text_for_writing,
)
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
    SummarizedStats,
    sort_coverage,
)

from . import versions

LOGGER = logging.getLogger("gcovr")

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


def write_report(covdata: CovData, output_file: str, options: Options) -> None:
    r"""produce an JSON report in the format partially
    compatible with gcov JSON output"""

    gcovr_json_root = {
        "gcovr/format_version": versions.JSON_FORMAT_VERSION,
        "files": _json_from_files(covdata, options),
    }

    _write_json_result(
        gcovr_json_root, output_file, "coverage.json", options.json_pretty
    )


def write_summary_report(covdata, output_file: str, options: Options):
    """Produce gcovr JSON summary report"""

    json_dict = {}

    json_dict["root"] = os.path.relpath(
        options.root,
        os.getcwd() if output_file == "-" else os.path.dirname(output_file),
    )
    json_dict["gcovr/summary_format_version"] = versions.JSON_SUMMARY_FORMAT_VERSION
    json_dict["files"] = []

    # Data
    keys = sort_coverage(
        covdata,
        sort_key=options.sort_key,
        sort_reverse=options.sort_reverse,
        by_metric="branch" if options.sort_branches else "line",
    )

    for key in keys:
        filename = presentable_filename(covdata[key].filename, options.root_filter)
        if options.json_base:
            filename = "/".join([options.json_base, filename])

        json_dict["files"].append(
            {
                "filename": filename,
                **_summary_from_stats(
                    SummarizedStats.from_file(covdata[key]), None, options
                ),
            }
        )

    # Footer & summary
    json_dict.update(
        _summary_from_stats(SummarizedStats.from_covdata(covdata), 0.0, options)
    )

    _write_json_result(
        json_dict, output_file, "summary_coverage.json", options.json_summary_pretty
    )


def _summary_from_stats(
    stats: SummarizedStats, default, options: Options
) -> Dict[str, Any]:
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

    if options.show_decision:
        json_dict["decision_total"] = stats.decision.total
        json_dict["decision_covered"] = stats.decision.covered
        json_dict["decision_percent"] = stats.decision.percent_or(default)

    return json_dict


def _json_from_files(files: CovData, options) -> list:
    return [_json_from_file(files[key], options) for key in sorted(files)]


def _json_from_file(file: FileCoverage, options) -> dict:
    filename = presentable_filename(file.filename, options.root_filter)
    if options.json_base:
        filename = "/".join([options.json_base, filename])
    return {
        "file": filename,
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
    }
    if line.excluded:
        json_line["gcovr/excluded"] = True
    if line.md5:
        json_line["gcovr/md5"] = line.md5
    if line.decision is not None:
        json_line["gcovr/decision"] = _json_from_decision(line.decision)
    if len(line.calls) > 0:
        json_line["gcovr/calls"] = _json_from_calls(line.calls)

    return json_line


def _json_from_branches(branches: Dict[int, BranchCoverage]) -> list:
    return [_json_from_branch(branches[no]) for no in sorted(branches)]


def _json_from_branch(branch: BranchCoverage) -> dict:
    return {
        "blockno": branch.blockno,
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


def _json_from_calls(calls: Dict[int, CallCoverage]) -> list:
    return [_json_from_call(calls[no]) for no in sorted(calls)]


def _json_from_call(call: CallCoverage) -> dict:
    return {"covered": call.covered, "callno": call.callno}


def _json_from_functions(functions: Dict[str, FunctionCoverage]) -> list:
    return [
        f for name in sorted(functions) for f in _json_from_function(functions[name])
    ]


def _json_from_function(function: FunctionCoverage) -> list:
    json_functions = []
    for lineno, count in function.count.items():
        json_function = {
            "name": function.name,
            "lineno": lineno,
            "execution_count": count,
            "returned_count": function.returned[lineno],
            "blocks_percent": function.blocks[lineno],
        }
        if function.excluded[lineno]:
            json_function["gcovr/excluded"] = True

        json_functions.append(json_function)

    return json_functions
