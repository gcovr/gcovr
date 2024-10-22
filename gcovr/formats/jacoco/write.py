# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
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

# cspell:ignore sourcefilename

from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Dict
from lxml import etree  # nosec # We only write XML files

from ...options import Options

from ...utils import force_unix_separator, open_binary_for_writing, presentable_filename
from ...coverage import CovData, CoverageStat, LineCoverage, SummarizedStats


def write_report(covdata: CovData, output_file: str, options: Options) -> None:
    """produce an XML report in the JaCoCo format"""

    stats = SummarizedStats.from_covdata(covdata)

    root = etree.Element("report")

    # Generate the coverage output (on a per-package basis)
    packages: Dict[str, PackageData] = {}

    for fname in sorted(covdata):
        filecov = covdata[fname]
        filename = presentable_filename(fname, root_filter=options.root_filter)
        if "/" in filename:
            directory, fname = filename.rsplit("/", 1)
        else:
            directory, fname = "", filename

        package = packages.setdefault(
            directory,
            PackageData(
                {},
                CoverageStat.new_empty(),
                CoverageStat.new_empty(),
            ),
        )
        class_elem = etree.Element("class")
        lines = etree.SubElement(class_elem, "lines")

        for linecov in filecov.lines.values():
            if linecov.is_reportable:
                lines.append(_line_element(linecov))

        stats = SummarizedStats.from_file(filecov)

        class_name = fname.replace(".", "_")
        class_elem.set("name", class_name)
        class_elem.set(
            "sourcefilename", force_unix_separator(os.path.join(options.root, filename))
        )
        class_elem.append(_counter_element("LINE", stats.line))
        class_elem.append(_counter_element("BRANCH", stats.branch))

        package.classes_xml[class_name] = class_elem
        package.line += stats.line
        package.branch += stats.branch

    for package_name in sorted(packages):
        package_data = packages[package_name]
        package_elem = etree.Element("package")
        root.append(package_elem)
        for class_name in sorted(package_data.classes_xml):
            package_elem.append(package_data.classes_xml[class_name])
        package_elem.append(_counter_element("LINE", package_data.line))
        package_elem.append(_counter_element("BRANCH", package_data.branch))
        package_elem.set("name", package_name.replace("/", "."))

    root.append(_counter_element("LINE", stats.line))
    root.append(_counter_element("BRANCH", stats.branch))

    with open_binary_for_writing(output_file, "jacoco.xml") as fh:
        fh.write(
            etree.tostring(
                root,
                pretty_print=options.jacoco_pretty,
                encoding="UTF-8",
                xml_declaration=True,
                doctype="<!DOCTYPE coverage SYSTEM 'https://www.jacoco.org/jacoco/trunk/coverage/report.dtd'>",
            )
        )


@dataclass
class PackageData:
    classes_xml: Dict[str, etree.Element]
    line: CoverageStat
    branch: CoverageStat


def _counter_element(element_type: str, stat: CoverageStat) -> etree.Element:
    """format a CoverageStat as a string in range 0.0 to 1.0 inclusive"""
    counter_elem = etree.Element("counter")
    counter_elem.set("type", element_type)
    counter_elem.set("missed", str(stat.total - stat.covered))
    counter_elem.set("covered", str(stat.covered))

    return counter_elem


def _line_element(line: LineCoverage) -> etree.Element:
    stat = line.branch_coverage()

    line_elem = etree.Element("line")
    line_elem.set("nr", str(line.lineno))

    if stat.total:
        line_elem.set("mb", str(stat.total - stat.covered))
        line_elem.set("cb", str(stat.covered))

    return line_elem
