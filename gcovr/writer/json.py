# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
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
import functools

from .base import Base
from .utils import (
    get_global_stats,
    open_text_for_writing,
    presentable_filename,
    sort_coverage,
    summarize_file_coverage,
)
from ..configuration import GcovrConfigOption


JSON_FORMAT_VERSION = "0.2"
JSON_SUMMARY_FORMAT_VERSION = "0.2"
PRETTY_JSON_INDENT = 4


class Json(Base):
    def options(self):
        yield GcovrConfigOption(
            "json",
            ["--json"],
            group="output_options",
            metavar="OUTPUT",
            help="Generate a JSON report. "
            "OUTPUT is optional and defaults to --output.",
            nargs="?",
            type=GcovrConfigOption.OutputOrDefault,
            default=None,
            const=GcovrConfigOption.OutputOrDefault(None),
        )
        yield GcovrConfigOption(
            "json_pretty",
            ["--json-pretty"],
            group="output_options",
            help="Pretty-print the JSON report. Implies --json. Default: {default!s}.",
            action="store_true",
        )
        yield GcovrConfigOption(
            "json_summary",
            ["--json-summary"],
            group="output_options",
            metavar="OUTPUT",
            help="Generate a JSON summary report. "
            "OUTPUT is optional and defaults to --output.",
            nargs="?",
            type=GcovrConfigOption.OutputOrDefault,
            default=None,
            const=GcovrConfigOption.OutputOrDefault(None),
        )
        yield GcovrConfigOption(
            "json_summary_pretty",
            ["--json-summary-pretty"],
            group="output_options",
            help="Pretty-print the JSON SUMMARY report. Implies --json-summary. Default: {default!s}.",
            action="store_true",
        )

    def writers(self, options, logger):
        if options.json or options.json_pretty:
            yield (
                [options.json],
                print_report,
                lambda: logger.warn(
                    "JSON output skipped - "
                    "consider providing output file with `--json=OUTPUT`."
                ),
            )

        if options.json_summary or options.json_summary_pretty:
            yield (
                [options.json_summary],
                print_summary_report,
                lambda: logger.warn(
                    "JSON summary output skipped - "
                    "consider providing output file with `--json-summary=OUTPUT`."
                ),
            )


def print_report(covdata, output_file, options):
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
        gcovr_json_root["files"].append(gcovr_json_file)

    _write_json_result(
        gcovr_json_root, output_file, "coverage.json", options.json_pretty
    )


def print_summary_report(covdata, output_file, options):

    json_dict = {}

    json_dict["root"] = os.path.relpath(
        options.root, os.getcwd() if output_file == "-" else output_file
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
        (
            filename,
            line_total,
            line_covered,
            line_percent,
            branch_total,
            branch_covered,
            branch_percent,
        ) = summarize_file_coverage(covdata[key], options.root_filter)

        json_dict["files"].append(
            {
                "filename": filename,
                "line_total": line_total,
                "line_covered": line_covered,
                "line_percent": line_percent,
                "branch_total": branch_total,
                "branch_covered": branch_covered,
                "branch_percent": branch_percent,
            }
        )

    (
        lines_total,
        lines_covered,
        lines_percent,
        branches_total,
        branches_covered,
        branches_percent,
    ) = get_global_stats(covdata)

    # Footer & summary
    json_dict["line_total"] = lines_total
    json_dict["line_covered"] = lines_covered
    json_dict["line_percent"] = lines_percent

    json_dict["branch_total"] = branches_total
    json_dict["branch_covered"] = branches_covered
    json_dict["branch_percent"] = branches_percent

    _write_json_result(
        json_dict, output_file, "summary_coverage.json", options.json_summary_pretty
    )


def _write_json_result(gcovr_json_dict, output_file, default_filename, pretty):
    r"""helper utility to output json format dictionary to a file/STDOUT """
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


def _json_from_lines(lines):
    json_lines = [_json_from_line(lines[no]) for no in sorted(lines)]
    return json_lines


def _json_from_line(line):
    json_line = {}
    json_line["branches"] = _json_from_branches(line.branches)
    json_line["count"] = line.count
    json_line["line_number"] = line.lineno
    json_line["gcovr/noncode"] = line.noncode
    return json_line


def _json_from_branches(branches):
    json_branches = [_json_from_branch(branches[no]) for no in sorted(branches)]
    return json_branches


def _json_from_branch(branch):
    json_branch = {}
    json_branch["count"] = branch.count
    json_branch["fallthrough"] = bool(branch.fallthrough)
    json_branch["throw"] = bool(branch.throw)
    return json_branch
