# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.2
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

import logging
import os
from glob import glob
from lxml import etree  # nosec # We only write XML files

from ...options import Options
from ..gcov.read import apply_filter_include_exclude
from ...coverage import (
    BranchCoverage,
    CovData,
    FileCoverage,
    LineCoverage,
)
from ...merging import (
    get_merge_mode_from_options,
    insert_branch_coverage,
    insert_file_coverage,
    insert_line_coverage,
)

LOGGER = logging.getLogger("gcovr")


#
#  Get coverage from already existing gcovr JSON files
#
def read_report(options: Options) -> CovData:
    """merge a coverage from multiple reports in the format
    compatible with Cobertura"""

    if len(options.cobertura_add_tracefile) == 0:
        return None

    datafiles = set()

    for trace_files_regex in options.cobertura_add_tracefile:
        trace_files = glob(trace_files_regex, recursive=True)
        if not trace_files:
            raise RuntimeError(
                "Bad --covertura-add-tracefile option.\n"
                "\tThe specified file does not exist."
            )
        else:
            for trace_file in trace_files:
                datafiles.add(os.path.normpath(trace_file))

    covdata = dict()
    for filename in datafiles:
        LOGGER.debug(f"Processing XML file: {filename}")

        try:
            root = etree.parse(
                filename
            ).getroot()  # nosec # We parse the file given by the user
        except Exception as e:
            raise RuntimeError(f"Bad --cobertura-add-tracefile option.\n{e}")

        for gcovr_file in root.xpath("./packages//class"):
            if gcovr_file.get("filename") is None:  # pragma: no cover
                LOGGER.warning(
                    f"Missing filename attribute in class element of {filename}"
                )
                continue

            file_path = os.path.join(
                os.path.abspath(options.root),
                os.path.normpath(gcovr_file.get("filename")),
            )

            filtered, excluded = apply_filter_include_exclude(
                file_path, options.filter, options.exclude
            )

            # Ignore if the filename does not match the filter
            if filtered:  # pragma: no cover
                LOGGER.debug(f"  Filtering coverage data for file {file_path}")
                continue

            # Ignore if the filename matches the exclude pattern
            if excluded:  # pragma: no cover
                LOGGER.debug(f"  Excluding coverage data for file {file_path}")
                continue

            file_coverage = FileCoverage(file_path)
            merge_options = get_merge_mode_from_options(options)
            for xml_line in gcovr_file.xpath("./lines//line"):
                insert_line_coverage(file_coverage, _line_from_xml(filename, xml_line))

            insert_file_coverage(covdata, file_coverage, merge_options)

    return covdata


def _line_from_xml(filename: str, xml_line) -> LineCoverage:
    try:
        lineno = int(xml_line.get("number"))
    except Exception:  # pragma: no cover
        raise RuntimeError(
            "Bad --covertura-add-tracefile option.\n"
            f"'number' attribute is required and must be an integer: {etree.tostring(xml_line).decode()}\n"
        )

    try:
        count = int(xml_line.get("hits"))
    except Exception:  # pragma: no cover
        raise RuntimeError(
            "Bad --covertura-add-tracefile option.\n"
            f"'hits' attribute is required and must be an integer: {etree.tostring(xml_line).decode()}\n"
        )

    is_branch = xml_line.get("branch") == "true"
    branch_msg = xml_line.get("condition-coverage")
    line = LineCoverage(lineno, count=count)

    if is_branch and branch_msg is not None:
        try:
            [covered, total] = branch_msg[branch_msg.rfind("(") + 1 : -1].split("/")
            for i in range(int(total)):
                insert_branch_coverage(line, i, _branch_from_json(i, i < int(covered)))
        except Exception:  # pragma: no cover
            LOGGER.warning(
                f"Invalid branch information for line {line.lineno} in file {filename}"
            )

    return line


def _branch_from_json(blockno: int, is_covered: bool) -> BranchCoverage:
    return BranchCoverage(
        blockno=blockno,
        count=1 if is_covered else 0,
    )
