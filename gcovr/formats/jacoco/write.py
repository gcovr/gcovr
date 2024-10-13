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

    for f in sorted(covdata):
        data = covdata[f]
        filename = presentable_filename(f, root_filter=options.root_filter)
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
        c = etree.Element("class")
        lines = etree.SubElement(c, "lines")

        # TODO should use FileCoverage.branch_coverage() calculation
        class_branch = CoverageStat(0, 0)
        for lineno in sorted(data.lines):
            line_cov = data.lines[lineno]
            if not line_cov.is_reportable:
                continue

            b = line_cov.branch_coverage()
            if b.total:
                class_branch += b

            lines.append(_line_element(line_cov))

        stats = SummarizedStats.from_file(data)

        className = fname.replace(".", "_")
        c.set("name", className)
        c.set(
            "sourcefilename", force_unix_separator(os.path.join(options.root, filename))
        )
        c.append(_counter_element("LINE", stats.line))
        c.append(_counter_element("BRANCH", class_branch))

        package.classes_xml[className] = c
        package.line += stats.line
        package.branch += class_branch

    for packageName in sorted(packages):
        packageData = packages[packageName]
        package = etree.Element("package")
        root.append(package)
        for className in sorted(packageData.classes_xml):
            package.append(packageData.classes_xml[className])
        package.append(_counter_element("LINE", packageData.line))
        package.append(_counter_element("BRANCH", packageData.branch))
        package.set("name", packageName.replace("/", "."))

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


def _counter_element(type: str, stat: CoverageStat) -> etree.Element:
    """format a CoverageStat as a string in range 0.0 to 1.0 inclusive"""
    elem = etree.Element("counter")
    elem.set("type", type)
    elem.set("missed", str(stat.total - stat.covered))
    elem.set("covered", str(stat.covered))

    return elem


def _line_element(line: LineCoverage) -> etree.Element:
    branch = line.branch_coverage()

    elem = etree.Element("line")
    elem.set("nr", str(line.lineno))

    if branch.total:
        elem.set("mb", str(branch.total - branch.covered))
        elem.set("cb", str(branch.covered))

    return elem
