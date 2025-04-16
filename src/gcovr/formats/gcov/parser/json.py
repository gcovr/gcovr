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

"""
Handle parsing of the json ``.gcov.json.gz`` file format.

Other modules should only use the following items:
`parse_coverage()`

The behavior of this parser was informed by the following sources:

* the *Invoking Gcov* section in the GCC manual (version 11)
  <https://gcc.gnu.org/onlinedocs/gcc-14.1.0/gcc/Invoking-Gcov.html>
"""
# pylint: disable=too-many-lines
# cspell:ignore getpreferredencoding

import logging
import os
from locale import getpreferredencoding
from typing import Any, Optional

from gcovr.utils import get_md5_hexdigest

from ....data_model.coverage import FileCoverage
from ....data_model.merging import FUNCTION_MAX_LINE_MERGE_OPTIONS, MergeOptions
from ....filter import Filter, is_file_excluded
from .common import (
    SUSPICIOUS_COUNTER,
    check_hits,
)

GCOV_JSON_VERSION = "2"
LOGGER = logging.getLogger("gcovr")
DEFAULT_SOURCE_ENCODING = getpreferredencoding()


def parse_coverage(
    data_fname: str,
    gcov_json_data: dict[str, Any],
    include_filters: list[Filter],
    exclude_filters: list[Filter],
    ignore_parse_errors: Optional[set[str]],
    suspicious_hits_threshold: int = SUSPICIOUS_COUNTER,
    source_encoding: str = DEFAULT_SOURCE_ENCODING,
) -> list[tuple[FileCoverage, list[str]]]:
    """Process a GCOV JSON output."""

    files_coverage = list[tuple[FileCoverage, list[str]]]()

    # Check format version because the file can be created external
    if gcov_json_data["format_version"] != GCOV_JSON_VERSION:
        raise RuntimeError(
            f"Got wrong JSON format version {gcov_json_data['format_version']}, expected {GCOV_JSON_VERSION}"
        )

    for file in gcov_json_data["files"]:
        source_lines: list[bytes] = []
        fname = os.path.normpath(
            os.path.join(gcov_json_data["current_working_directory"], file["file"])
        )
        LOGGER.debug(f"Parsing coverage data for file {fname}")

        if is_file_excluded(fname, include_filters, exclude_filters):
            continue

        max_line_number = file["lines"][-1]["line_number"] if file["lines"] else 1
        try:
            with open(fname, "rb") as fh_in2:
                source_lines = fh_in2.read().splitlines()
            lines = len(source_lines)
            if lines < max_line_number:
                LOGGER.warning(
                    f"File {max_line_number} has {lines} line(s) but coverage data has {max_line_number} line(s)."
                )
                # GCOV itself adds the /*EOF*/ in the text report if there is no data and we used the same.
                source_lines += [b"/*EOF*/"] * (max_line_number - lines)
        except OSError as e:
            if file["file"].endswith("<stdin>"):
                message = f"Got unreadable source file '{file['file']}', replacing with empty lines."
                LOGGER.info(message)
            else:
                # The exception contains the source file name,
                # e.g. [Errno 2] No such file or directory: 'xy.txt'
                message = f"Can't read file, using empty lines: {e}"
                LOGGER.warning(message)
            # If we can't read the file we use as first line the error
            # and use empty lines for the rest of the lines.
            source_lines = [b""] * max_line_number
            source_lines[0] = f"/* {message} */".encode()

        encoded_source_lines = [
            line.decode(source_encoding, errors="replace") for line in source_lines
        ]

        filecov = _parse_file_node(
            data_fname,
            gcov_file_node=file,
            filename=fname,
            source_lines=encoded_source_lines,
            ignore_parse_errors=ignore_parse_errors,
            suspicious_hits_threshold=suspicious_hits_threshold,
        )

        files_coverage.append((filecov, encoded_source_lines))

    return files_coverage


def _parse_file_node(
    data_fname: str,
    gcov_file_node: dict[str, Any],
    filename: str,
    source_lines: list[str],
    ignore_parse_errors: Optional[set[str]],
    suspicious_hits_threshold: int = SUSPICIOUS_COUNTER,
) -> FileCoverage:
    """
    Extract coverage data from a json gcov report.

    Logging:
    Parse problems are reported as warnings.
    Coverage exclusion decisions are reported as verbose messages.

    Arguments:
        gcov_file_node: one of the "files" node in the gcov json format
        filename: for error reports
        source_lines: decoded source code lines, for reporting
        data_fname: source of this node, for reporting
        ignore_parse_errors: which errors should be converted to warnings

    Returns:
        The coverage data

    Raises:
        Any exceptions during parsing, unless ignore_parse_errors is set.
    """
    persistent_states: dict[str, Any] = {"location": (filename, 0)}

    if ignore_parse_errors is None:
        ignore_parse_errors = set()

    filecov = FileCoverage(data_fname, filename=filename)
    for line in gcov_file_node["lines"]:
        persistent_states.update(location=(filename, line["line_number"]))
        linecov = filecov.insert_line_coverage(
            str(data_fname),
            lineno=line["line_number"],
            count=check_hits(
                line["count"],
                source_lines[line["line_number"] - 1],
                ignore_parse_errors,
                suspicious_hits_threshold,
                persistent_states,
            ),
            function_name=line.get("function_name"),
            block_ids=line["block_ids"],
            md5=get_md5_hexdigest(
                source_lines[line["line_number"] - 1].encode("UTF-8")
            ),
        )
        for index, branch in enumerate(line["branches"]):
            linecov.insert_branch_coverage(
                str(data_fname),
                branchno=index,
                count=check_hits(
                    branch["count"],
                    source_lines[line["line_number"] - 1],
                    ignore_parse_errors,
                    suspicious_hits_threshold,
                    persistent_states,
                ),
                source_block_id=branch["source_block_id"],
                fallthrough=branch["fallthrough"],
                throw=branch["throw"],
                destination_block_id=branch["destination_block_id"],
            )
        for index, condition in enumerate(line.get("conditions", [])):
            linecov.insert_condition_coverage(
                str(data_fname),
                conditionno=index,
                count=check_hits(
                    condition["count"],
                    source_lines[line["line_number"] - 1],
                    ignore_parse_errors,
                    suspicious_hits_threshold,
                    persistent_states,
                ),
                covered=condition["covered"],
                not_covered_true=condition["not_covered_true"],
                not_covered_false=condition["not_covered_false"],
            )
        for index, call in enumerate(line.get("calls", [])):
            linecov.insert_call_coverage(
                str(data_fname),
                callno=index,
                source_block_id=call["source_block_id"],
                destination_block_id=call["destination_block_id"],
                returned=call["returned"],
            )

    for function in gcov_file_node["functions"]:
        # Use 100% only if covered == total.
        if function["blocks_executed"] == function["blocks"]:
            blocks = 100.0
        else:
            # There is at least one uncovered item.
            # Round to 1 decimal and clamp to max 99.9%.
            ratio = function["blocks_executed"] / function["blocks"]
            blocks = min(99.9, round(ratio * 100.0, 1))

        filecov.insert_function_coverage(
            str(data_fname),
            MergeOptions(func_opts=FUNCTION_MAX_LINE_MERGE_OPTIONS),
            mangled_name=function["name"],
            demangled_name=function["demangled_name"],
            lineno=function["start_line"],
            count=function["execution_count"],
            blocks=blocks,
            start=(function["start_line"], function["start_column"]),
            end=(function["end_line"], function["end_column"]),
        )

    if (
        "negative_hits.warn_once_per_file" in persistent_states
        and persistent_states["negative_hits.warn_once_per_file"] > 1
    ):
        LOGGER.warning(
            f"Ignored {persistent_states['negative_hits.warn_once_per_file']} negative hits overall."
        )

    if (
        "suspicious_hits.warn_once_per_file" in persistent_states
        and persistent_states["suspicious_hits.warn_once_per_file"] > 1
    ):
        LOGGER.warning(
            f"Ignored {persistent_states['suspicious_hits.warn_once_per_file']} suspicious hits overall."
        )

    return filecov
