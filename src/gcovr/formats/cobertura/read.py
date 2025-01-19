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

import logging
import os
from glob import glob
from lxml import etree  # nosec # We only write XML files

from ...coverage import (
    BranchCoverage,
    CoverageContainer,
    FileCoverage,
    LineCoverage,
)
from ...filter import is_file_excluded
from ...merging import (
    get_merge_mode_from_options,
    insert_branch_coverage,
    insert_file_coverage,
    insert_line_coverage,
)
from ...options import Options

LOGGER = logging.getLogger("gcovr")


#
#  Get coverage from already existing gcovr JSON files
#
def read_report(options: Options) -> CoverageContainer:
    """merge a coverage from multiple reports in the format
    compatible with Cobertura"""

    covdata = CoverageContainer()
    if len(options.cobertura_add_tracefile) == 0:
        return covdata

    datafiles = set()

    for trace_files_regex in options.cobertura_add_tracefile:
        trace_files = glob(trace_files_regex, recursive=True)
        if not trace_files:
            raise RuntimeError(
                "Bad --covertura-add-tracefile option.\n"
                "\tThe specified file does not exist."
            )

        for trace_file in trace_files:
            datafiles.add(os.path.normpath(trace_file))

    for data_source_filename in datafiles:
        LOGGER.debug(f"Processing XML file: {data_source_filename}")

        try:
            root: etree._Element = etree.parse(data_source_filename).getroot()  # nosec # We parse the file given by the user
        except Exception as e:
            raise RuntimeError(f"Bad --cobertura-add-tracefile option.\n{e}") from None

        source_elem = root.find("./sources/source")
        if source_elem is None:
            raise AssertionError(
                f"No source directory defined in file {data_source_filename}"
            )
        source_dir = str(source_elem.text)

        gcovr_file: etree._Element
        for gcovr_file in root.xpath("./packages//class"):  # type: ignore [assignment, union-attr]
            filename = gcovr_file.get("filename")
            if filename is None:  # pragma: no cover
                LOGGER.warning(
                    f"Missing filename attribute in class element at {data_source_filename}:{gcovr_file.sourceline}"
                )
                continue

            filename = str(os.path.normpath(os.path.join(source_dir, filename)))
            if is_file_excluded(filename, options.filter, options.exclude):
                continue

            filecov = FileCoverage(filename, data_source_filename)
            merge_options = get_merge_mode_from_options(options)
            xml_line: etree._Element
            for xml_line in gcovr_file.xpath("./lines//line"):  # type: ignore [assignment, union-attr]
                insert_line_coverage(
                    filecov, _line_from_xml(data_source_filename, xml_line)
                )

            insert_file_coverage(covdata, filecov, merge_options)

    return covdata


def _line_from_xml(filename: str, xml_line: etree._Element) -> LineCoverage:
    try:
        lineno = int(xml_line.get("number", ""))
    except Exception:  # pragma: no cover
        raise RuntimeError(
            "Bad --covertura-add-tracefile option.\n"
            f"'number' attribute is required and must be an integer: {etree.tostring(xml_line).decode()}\n"
        ) from None

    try:
        count = int(xml_line.get("hits", ""))
    except Exception:  # pragma: no cover
        raise RuntimeError(
            "Bad --covertura-add-tracefile option.\n"
            f"'hits' attribute is required and must be an integer: {etree.tostring(xml_line).decode()}\n"
        ) from None

    is_branch = xml_line.get("branch") == "true"
    branch_msg = xml_line.get("condition-coverage")
    linecov = LineCoverage(lineno, count=count)

    if is_branch and branch_msg is not None:
        try:
            [covered, total] = branch_msg[branch_msg.rfind("(") + 1 : -1].split("/")
            for i in range(int(total)):
                insert_branch_coverage(
                    linecov, i, _branch_from_json(i, i < int(covered))
                )
        except AssertionError:  # pragma: no cover
            LOGGER.warning(
                f"Invalid branch information for line {linecov.lineno} in file {filename}"
            )

    return linecov


def _branch_from_json(block_id: int, is_covered: bool) -> BranchCoverage:
    return BranchCoverage(
        source_block_id=block_id,
        count=1 if is_covered else 0,
    )
