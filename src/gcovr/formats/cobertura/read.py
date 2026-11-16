#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.8+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

"""GCOVR Cobertura report."""

from glob import glob
from pathlib import Path

from lxml import etree  # nosec # We only write XML files

from ...data_model.container import CoverageContainer
from ...data_model.coverage import (
    BranchCoverage,
    FileCoverage,
    LineCoverage,
)
from ...data_model.merging import MergeOptions, get_merge_mode_from_options
from ...filter import is_file_excluded
from ...logging import LOGGER
from ...options import Options


#
#  Get coverage from already existing gcovr JSON files
#
def read_report(options: Options) -> CoverageContainer:
    """Merge a coverage from multiple reports in the format compatible with Cobertura."""
    covdata = CoverageContainer(options.root_dir)
    if len(options.cobertura_tracefile) == 0:
        return covdata

    datafiles = list[Path]()

    for trace_file_glob in options.cobertura_tracefile:
        root_dir = trace_file_glob.parent
        trace_files = [
            (root_dir / e)
            for e in sorted(
                glob(  # noqa: PTH207
                    trace_file_glob.name,
                    root_dir=str(root_dir),
                    recursive=True,
                )
            )
        ]
        if not trace_files:
            msg = (
                "Bad --covertura-add-tracefile option.\n"
                "\tThe specified file does not exist."
            )
            raise RuntimeError(msg)

        for trace_file in trace_files:
            if trace_file not in datafiles:
                datafiles.append(trace_file)

    for data_source in datafiles:
        LOGGER.debug("Processing XML file: %s", data_source)

        try:
            root: etree._Element = etree.parse(data_source).getroot()  # nosec # We parse the file given by the user
        except Exception as e:  # noqa: BLE001
            msg = f"Bad --cobertura-add-tracefile option.\n{e}"
            raise RuntimeError(msg) from None

        source_elem = root.find("./sources/source")
        if source_elem is None:
            msg = f"No source directory defined in file {data_source}"
            raise AssertionError(msg)
        source_dir = Path(str(source_elem.text))

        gcovr_file: etree._Element
        for gcovr_file in root.xpath("./packages//class"):  # type: ignore [assignment, union-attr]
            filename_str = gcovr_file.get("filename")
            if filename_str is None:  # pragma: no cover
                LOGGER.warning(
                    "Missing filename attribute in class element at %s:%s",
                    data_source,
                    gcovr_file.sourceline,
                )
                continue

            filename = source_dir / filename_str
            if is_file_excluded(
                "source file", filename, options.include_filter, options.exclude_filter
            ):
                continue

            filecov = FileCoverage(data_source, filename=filename)
            merge_options = get_merge_mode_from_options(options)
            xml_line: etree._Element
            for xml_line in gcovr_file.xpath("./lines//line"):  # type: ignore [assignment, union-attr]
                _insert_line_from_xml(filecov, data_source, merge_options, xml_line)

            covdata.insert_file_coverage(filecov, merge_options)

    return covdata


def _insert_line_from_xml(
    filecov: FileCoverage,
    data_sources: Path,
    merge_options: MergeOptions,
    xml_line: etree._Element,
) -> None:
    try:
        lineno = int(xml_line.get("number", ""))
    except Exception:  # pragma: no cover  # noqa: BLE001
        msg = (
            "Bad --covertura-add-tracefile option.\n"
            f"'number' attribute is required and must be an integer: {etree.tostring(xml_line).decode()}\n"
        )
        raise RuntimeError(msg) from None

    try:
        count = int(xml_line.get("hits", ""))
    except Exception:  # pragma: no cover  # noqa: BLE001
        msg = (
            "Bad --covertura-add-tracefile option.\n"
            f"'hits' attribute is required and must be an integer: {etree.tostring(xml_line).decode()}\n"
        )
        raise RuntimeError(msg) from None

    is_branch = xml_line.get("branch") == "true"
    branch_msg = xml_line.get("condition-coverage")
    linecov = filecov.insert_line_coverage(
        data_sources, merge_options, lineno=lineno, count=count, function_name=None
    )

    if is_branch and branch_msg is not None:
        try:
            [covered, total] = branch_msg[branch_msg.rfind("(") + 1 : -1].split("/")
            for i in range(int(total)):
                _branch_from_json(linecov, data_sources, i, is_covered=i < int(covered))
        except AssertionError as exc:  # pragma: no cover
            LOGGER.warning(
                "Invalid branch information for line %s: %s", linecov.lineno, exc
            )


def _branch_from_json(
    linecov: LineCoverage, data_sources: Path, branchno: int, *, is_covered: bool
) -> BranchCoverage:
    return linecov.insert_branch_coverage(
        data_sources,
        branchno=branchno,
        count=1 if is_covered else 0,
    )
