# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 7.0+main, a parsing and reporting tool for gcov.
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

from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import Dict
from lxml import etree

from ...options import Options

from ...utils import (
    get_md5_hexdigest,
    open_binary_for_writing,
    presentable_filename,
)
from ...coverage import CovData, CoverageStat, LineCoverage, SummarizedStats

LOGGER = logging.getLogger("gcovr")


def write_report(covdata: CovData, output_file: str, options: Options) -> None:
    """produce an XML report in the Cobertura format"""

    stats = SummarizedStats.from_covdata(covdata)
    timestamp = str(int(options.timestamp.timestamp()))

    root = etree.Element("coverage")
    root.set("clover", timestamp)
    root.set("generated", timestamp)

    project_elem = etree.SubElement(root, "project")
    if options.clover_project:
        project_elem.set("name", options.clover_project)
    project_elem.set("timestamp", timestamp)
    project_metrics = _metrics_element()
    project_elem.append(project_metrics)

    # Generate the coverage output (on a per-package basis)
    packages: Dict[str, PackageData] = {}

    for f in sorted(covdata):
        data = covdata[f]
        filename = presentable_filename(f, root_filter=options.root_filter)
        if "/" in filename:
            directory, fname = filename.rsplit("/", 1)
        else:
            directory, fname = "root", filename

        package_elem = packages.setdefault(
            directory,
            PackageData({}, CoverageStat.new_empty(), 0, 0),
        )
        file_elem = etree.Element("file")
        file_metrics = _metrics_element()
        file_elem.append(file_metrics)
        class_elem = etree.SubElement(file_elem, "class")
        class_elem.set("name", f"id${get_md5_hexdigest(filename.encode())}")
        class_metrics = _metrics_element()
        class_elem.append(class_metrics)

        ncloc = 0
        covered_elements = 0
        for lineno in sorted(data.lines):
            line_cov = data.lines[lineno]
            if not line_cov.is_reportable:
                continue
            ncloc += 1
            if line_cov.is_covered:
                covered_elements += 1
            file_elem.append(_line_element(line_cov))

        stats = SummarizedStats.from_file(data)

        file_elem.set("name", fname)
        file_elem.set("path", filename)

        file_metrics.set("classes", "1")
        file_metrics.set("loc", str(lineno))
        file_metrics.set("ncloc", str(ncloc))
        file_metrics.set("coveredelements", str(covered_elements))

        package_elem.files_xml[fname] = file_elem
        package_elem.line += stats.line
        package_elem.loc += lineno
        package_elem.ncloc += ncloc

    project_metrics.set("packages", str(len(packages)))

    for packageName in sorted(packages):
        packageData = packages[packageName]
        package_elem = etree.SubElement(project_elem, "package")
        package_metrics = _metrics_element()
        package_elem.append(package_metrics)
        number_files = str(len(packageData.files_xml))
        package_metrics.set("files", number_files)
        package_metrics.set("classes", number_files)
        package_metrics.set("loc", str(packageData.loc))
        package_metrics.set("ncloc", str(packageData.ncloc))
        for fname in sorted(packageData.files_xml):
            package_elem.append(packageData.files_xml[fname])
        package_elem.set("name", packageName.replace("/", "."))

    # WTH is this needed???
    testproject_elem = etree.SubElement(root, "testproject")
    testproject_elem.set("timestamp", timestamp)
    testproject_metrics = _metrics_element()
    testproject_elem.append(testproject_metrics)
    package_elem = etree.SubElement(testproject_elem, "package")
    package_elem.set("name", "dummy")
    package_metrics = _metrics_element()
    package_elem.append(package_metrics)
    file_elem = etree.Element("file")
    file_elem.set("name", "dummy")
    file_elem.set("path", "dummy")
    package_elem.append(file_elem)
    file_metrics = _metrics_element()
    file_elem.append(file_metrics)
    class_elem = etree.SubElement(file_elem, "class")
    class_elem.set("name", f"id${get_md5_hexdigest(b'dummy')}")
    class_metrics = _metrics_element()
    class_elem.append(class_metrics)

    with open_binary_for_writing(output_file, "clover.xml") as fh:
        fh.write(
            etree.tostring(
                root,
                pretty_print=options.clover_pretty,
                encoding="UTF-8",
                xml_declaration=True,
                # doctype="<!DOCTYPE coverage SYSTEM 'https://bitbucket.org/atlassian/clover/raw/a688248db8ae15eb7158947b7ba275c9ffbaf008/etc/schema/clover.xsd'>",
            )
        )


@dataclass
class PackageData:
    files_xml: Dict[str, etree.Element]
    line: CoverageStat
    loc: int
    ncloc: int


def _metrics_element() -> etree.Element:
    elem = etree.Element("metrics")
    for metric in [
        "complexity",
        "elements",
        "coveredelements",
        "conditionals",
        "coveredconditionals",
        "statements",
        "coveredstatements",
        "coveredmethods",
        "methods",
    ]:
        elem.set(metric, "0")

    return elem


def _line_element(line: LineCoverage) -> etree.Element:
    elem = etree.Element("line")
    elem.set("num", str(line.lineno))
    elem.set("type", "stmt")
    elem.set("count", str(line.count))

    return elem
