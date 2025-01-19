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
from typing import (
    Any,
    Optional,
    Union,
)

from gcovr.utils import get_md5_hexdigest

from ....coverage import (
    BranchCoverage,
    ConditionCoverage,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
)
from ....filter import Filter, is_file_excluded
from ....merging import (
    FUNCTION_MAX_LINE_MERGE_OPTIONS,
    MergeOptions,
    insert_branch_coverage,
    insert_condition_coverage,
    insert_function_coverage,
    insert_line_coverage,
)
from .common import (
    SUSPICIOUS_COUNTER,
    check_hits,
)

GCOV_JSON_VERSION = "2"
LOGGER = logging.getLogger("gcovr")
DEFAULT_SOURCE_ENCODING = getpreferredencoding()


def parse_coverage(
    gcov_json_data: dict[str, Any],
    include_filters: list[Filter],
    exclude_filters: list[Filter],
    ignore_parse_errors: Optional[set[str]],
    data_fname: Optional[str] = None,
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

        if file["file"] == "<stdin>":
            message = f"Got sourcefile {file['file']}, using empty lines."
            LOGGER.info(message)
            source_lines = [b"" for _ in range(file["lines"][-1]["line_number"])]
            source_lines[0] = f"/* {message} */".encode()
        else:
            with open(fname, "rb") as fh_in2:
                source_lines = fh_in2.read().splitlines()
            lines = len(source_lines)
            max_line_from_cdata = (
                file["lines"][-1]["line_number"] if file["lines"] else 1
            )
            if lines < max_line_from_cdata:
                LOGGER.warning(
                    f"File {fname} has {lines} line(s) but coverage data has {max_line_from_cdata} line(s)."
                )
                # Python ranges are exclusive. We want to iterate over all lines, including
                # that last line. Thus, we have to add a +1 to include that line.
                for _ in range(lines, max_line_from_cdata):
                    source_lines.append(b"/*EOF*/")

        encoded_source_lines = [
            line.decode(source_encoding, errors="replace") for line in source_lines
        ]

        file_cov = _parse_file_node(
            gcov_file_node=file,
            filename=fname,
            source_lines=encoded_source_lines,
            data_fname=data_fname,
            ignore_parse_errors=ignore_parse_errors,
            suspicious_hits_threshold=suspicious_hits_threshold,
        )

        files_coverage.append((file_cov, encoded_source_lines))

    return files_coverage


def _parse_file_node(
    gcov_file_node: dict[str, Any],
    filename: str,
    source_lines: list[str],
    data_fname: Optional[Union[str, set[str]]],
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
    persistent_states = dict[str, Any]()
    if ignore_parse_errors is None:
        ignore_parse_errors = set()

    file_cov = FileCoverage(filename, data_fname)
    for line in gcov_file_node["lines"]:
        line_cov = insert_line_coverage(
            file_cov,
            LineCoverage(
                line["line_number"],
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
                    source_lines[line["line_number"] - 1].encode("utf-8")
                ),
            ),
        )
        for index, branch in enumerate(line["branches"]):
            insert_branch_coverage(
                line_cov,
                index,
                BranchCoverage(
                    branch["source_block_id"],
                    check_hits(
                        branch["count"],
                        source_lines[line["line_number"] - 1],
                        ignore_parse_errors,
                        suspicious_hits_threshold,
                        persistent_states,
                    ),
                    fallthrough=branch["fallthrough"],
                    throw=branch["throw"],
                    destination_block_id=branch["destination_block_id"],
                ),
            )
        for index, condition in enumerate(line.get("conditions", [])):
            insert_condition_coverage(
                line_cov,
                index,
                ConditionCoverage(
                    check_hits(
                        condition["count"],
                        source_lines[line["line_number"] - 1],
                        ignore_parse_errors,
                        suspicious_hits_threshold,
                        persistent_states,
                    ),
                    condition["covered"],
                    condition["not_covered_true"],
                    condition["not_covered_false"],
                ),
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

        insert_function_coverage(
            file_cov,
            FunctionCoverage(
                function["name"],
                function["demangled_name"],
                lineno=function["start_line"],
                count=function["execution_count"],
                blocks=blocks,
                start=(function["start_line"], function["start_column"]),
                end=(function["end_line"], function["end_column"]),
            ),
            MergeOptions(func_opts=FUNCTION_MAX_LINE_MERGE_OPTIONS),
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

    return file_cov
