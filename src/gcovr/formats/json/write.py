# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
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
import functools
from typing import Any, Callable, Optional

from ...data_model.container import CoverageContainer
from ...data_model.coverage import (
    BranchesKeyType,
    CoverageBase,
    LinesKeyType,
    BranchCoverage,
    ConditionCoverage,
    DecisionCoverage,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
    CallCoverage,
)
from ...data_model.stats import SummarizedStats
from ...options import Options
from ...utils import (
    force_unix_separator,
    presentable_filename,
    open_text_for_writing,
)

from . import versions

LOGGER = logging.getLogger("gcovr")

PRETTY_JSON_INDENT = 4


def _write_json_result(
    gcovr_json_dict: dict[str, Any],
    output_file: str,
    default_filename: str,
    pretty: bool,
) -> None:
    r"""helper utility to output json format dictionary to a file/STDOUT"""
    write_json = json.dump

    if pretty:
        write_json = functools.partial(
            write_json,
            indent=PRETTY_JSON_INDENT,
            separators=(",", ": "),
        )
    else:
        write_json = functools.partial(write_json)

    with open_text_for_writing(output_file, default_filename) as fh:
        write_json(gcovr_json_dict, fh)


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    r"""produce an JSON report in the format partially
    compatible with gcov JSON output"""

    gcovr_json_root = {
        "gcovr/format_version": versions.JSON_FORMAT_VERSION,
        "files": _json_from_files(covdata, options),
    }

    _write_json_result(
        gcovr_json_root, output_file, "coverage.json", options.json_pretty
    )


def write_summary_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """Produce gcovr JSON summary report"""

    json_dict = dict[str, Any]()

    json_dict["root"] = force_unix_separator(
        os.path.relpath(
            options.root,
            os.getcwd() if output_file == "-" else os.path.dirname(output_file),
        )
    )
    json_dict["gcovr/summary_format_version"] = versions.JSON_SUMMARY_FORMAT_VERSION
    files = list[dict[str, Any]]()
    json_dict["files"] = files

    # Data
    sorted_keys = covdata.sort_coverage(
        sort_key=options.sort_key,
        sort_reverse=options.sort_reverse,
        by_metric="branch" if options.sort_branches else "line",
    )

    for key in sorted_keys:
        filename = presentable_filename(covdata[key].filename, options.root_filter)
        if options.json_base:
            filename = "/".join([options.json_base, filename])

        files.append(
            {
                "filename": filename,
                **_summary_from_stats(covdata[key].stats, None, options),
            }
        )

    # Footer & summary
    json_dict.update(_summary_from_stats(covdata.stats, 0.0, options))

    _write_json_result(
        json_dict, output_file, "summary_coverage.json", options.json_summary_pretty
    )


def _summary_from_stats(
    stats: SummarizedStats, default: Optional[float], options: Options
) -> dict[str, Any]:
    json_dict = dict[str, Any]()

    json_dict["line_total"] = stats.line.total
    json_dict["line_covered"] = stats.line.covered
    json_dict["line_percent"] = stats.line.percent_or(default)

    json_dict["function_total"] = stats.function.total
    json_dict["function_covered"] = stats.function.covered
    json_dict["function_percent"] = stats.function.percent_or(default)

    json_dict["branch_total"] = stats.branch.total
    json_dict["branch_covered"] = stats.branch.covered
    json_dict["branch_percent"] = stats.branch.percent_or(default)

    if stats.condition.total != 0:
        json_dict["condition_total"] = stats.condition.total
        json_dict["condition_covered"] = stats.condition.covered
        json_dict["condition_percent"] = stats.condition.percent_or(default)

    if options.show_decision:
        json_dict["decision_total"] = stats.decision.total
        json_dict["decision_covered"] = stats.decision.covered
        json_dict["decision_percent"] = stats.decision.percent_or(default)

    return json_dict


def _json_from_files(
    files: CoverageContainer, options: Options
) -> list[dict[str, Any]]:
    return [_json_from_file(files[key], options) for key in sorted(files)]


def _json_from_file(file: FileCoverage, options: Options) -> dict[str, Any]:
    # Only write data in verbose mode
    if options.verbose:

        def add_data_sources(json_data: dict[str, Any], cov: CoverageBase) -> None:
            """Return the printable data sources."""
            json_data["gcovr/data_sources"] = [
                [
                    presentable_filename(filename, options.root_filter)
                    for filename in data_source
                ]
                for data_source in sorted(cov.data_sources)
            ]
    else:

        def add_data_sources(json_data: dict[str, Any], cov: CoverageBase) -> None:  # pylint: disable=unused-argument
            """Stub if not running in verbose mode."""

    filename = presentable_filename(file.filename, options.root_filter)
    if options.json_base:
        filename = "/".join([options.json_base, filename])
    json_file = {
        "file": filename,
        "lines": _json_from_lines(file.lines, add_data_sources),
        "functions": _json_from_functions(file.functions, add_data_sources),
    }
    add_data_sources(json_file, file)

    return json_file


def _json_from_lines(
    lines: dict[LinesKeyType, LineCoverage],
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> list[dict[str, Any]]:
    return [_json_from_line(lines[no], add_data_sources) for no in sorted(lines)]


def _json_from_line(
    linecov: LineCoverage,
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> dict[str, Any]:
    json_line = dict[str, Any](
        {
            "line_number": linecov.lineno,
        }
    )
    if linecov.function_name is not None:
        json_line["function_name"] = linecov.function_name
    json_line.update(
        {
            "count": linecov.count,
            "branches": _json_from_branches(linecov.branches, add_data_sources),
        }
    )
    if linecov.conditions:
        json_line["conditions"] = _json_from_conditions(
            linecov.conditions, add_data_sources
        )
    if linecov.block_ids is not None:
        json_line["block_ids"] = linecov.block_ids
    if linecov.md5:
        json_line["gcovr/md5"] = linecov.md5
    if linecov.excluded:
        json_line["gcovr/excluded"] = True
    if linecov.decision is not None:
        json_line["gcovr/decision"] = _json_from_decision(
            linecov.decision, add_data_sources
        )
    if len(linecov.calls) > 0:
        json_line["gcovr/calls"] = _json_from_calls(linecov.calls, add_data_sources)
    add_data_sources(json_line, linecov)

    return json_line


def _json_from_branches(
    branches: dict[BranchesKeyType, BranchCoverage],
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> list[dict[str, Any]]:
    return [
        _json_from_branch(branches[no], add_data_sources) for no in sorted(branches)
    ]


def _json_from_branch(
    branchcov: BranchCoverage,
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> dict[str, Any]:
    json_branch = dict[str, Any]()
    json_branch.update(
        {
            "count": branchcov.count,
            "fallthrough": branchcov.fallthrough,
            "throw": branchcov.throw,
        }
    )
    if branchcov.source_block_id is not None:
        json_branch["source_block_id"] = branchcov.source_block_id
    if branchcov.destination_block_id is not None:
        json_branch["destination_block_id"] = branchcov.destination_block_id
    if branchcov.excluded is not None:
        json_branch["gcovr/excluded"] = branchcov.excluded
    add_data_sources(json_branch, branchcov)

    return json_branch


def _json_from_conditions(
    conditions: dict[int, ConditionCoverage],
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> list[dict[str, Any]]:
    return [
        _json_from_condition(conditions[no], add_data_sources)
        for no in sorted(conditions)
    ]


def _json_from_condition(
    conditioncov: ConditionCoverage,
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> dict[str, Any]:
    json_condition = {
        "count": conditioncov.count,
        "covered": conditioncov.covered,
        "not_covered_false": conditioncov.not_covered_false,
        "not_covered_true": conditioncov.not_covered_true,
    }
    add_data_sources(json_condition, conditioncov)

    return json_condition


def _json_from_decision(
    decisioncov: DecisionCoverage,
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> dict[str, Any]:
    json_decision: dict[str, Any]
    if isinstance(decisioncov, DecisionCoverageUncheckable):
        json_decision = {"type": "uncheckable"}
    elif isinstance(decisioncov, DecisionCoverageConditional):
        json_decision = {
            "type": "conditional",
            "count_true": decisioncov.count_true,
            "count_false": decisioncov.count_false,
        }
    elif isinstance(decisioncov, DecisionCoverageSwitch):
        json_decision = {
            "type": "switch",
            "count": decisioncov.count,
        }
    else:
        raise AssertionError(f"Unknown decision type: {decisioncov!r}")

    add_data_sources(json_decision, decisioncov)

    return json_decision


def _json_from_calls(
    calls: dict[int, CallCoverage],
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> list[dict[str, Any]]:
    return [_json_from_call(calls[no], add_data_sources) for no in sorted(calls)]


def _json_from_call(
    callcov: CallCoverage,
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> dict[str, Any]:
    json_call = dict[str, Any](
        {
            "callno": callcov.callno,
            "covered": callcov.covered,
        }
    )
    add_data_sources(json_call, callcov)

    return json_call


def _json_from_functions(
    functions: dict[str, FunctionCoverage],
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> list[dict[str, Any]]:
    return [
        f
        for name in sorted(functions)
        for f in _json_from_function(functions[name], add_data_sources)
    ]


def _json_from_function(
    functioncov: FunctionCoverage,
    add_data_sources: Callable[[dict[str, Any], CoverageBase], None],
) -> list[dict[str, Any]]:
    json_functions = list[dict[str, Any]]()
    for lineno, count in functioncov.count.items():
        json_function = dict[str, Any]()
        if functioncov.name is not None:
            json_function["name"] = functioncov.name
        if functioncov.demangled_name is not None:
            json_function["demangled_name"] = functioncov.demangled_name
        json_function.update(
            {
                "lineno": lineno,
                "execution_count": count,
                "blocks_percent": functioncov.blocks[lineno],
            }
        )
        if functioncov.start is not None and functioncov.end is not None:
            json_function["pos"] = (
                ":".join([str(e) for e in functioncov.start[lineno]]),
                ":".join([str(e) for e in functioncov.end[lineno]]),
            )
        if functioncov.excluded[lineno]:
            json_function["gcovr/excluded"] = True
        add_data_sources(json_function, functioncov)
        json_functions.append(json_function)

    return json_functions
