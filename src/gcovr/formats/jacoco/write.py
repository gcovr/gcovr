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

# cspell:ignore sourcefilename

from dataclasses import dataclass
import os
from lxml import etree  # nosec # We only write XML files

from ...options import Options

from ...utils import force_unix_separator, open_binary_for_writing, presentable_filename
from ...coverage import CoverageContainer, CoverageStat, LineCoverage, SummarizedStats


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce an XML report in the JaCoCo format"""

    root_elem = etree.Element("report")

    # Generate the coverage output (on a per-package basis)
    packages = dict[str, PackageData]()

    for fname in sorted(covdata):
        filecov = covdata[fname]
        filename = presentable_filename(fname, root_filter=options.root_filter)
        if "/" in filename:
            directory, fname = filename.rsplit("/", 1)
        else:
            directory, fname = "", filename

        package_data = packages.setdefault(
            directory,
            PackageData(
                {},
                SummarizedStats.new_empty(),
            ),
        )
        class_elem = etree.Element("class")
        lines_elem = etree.SubElement(class_elem, "lines")

        for linecov in filecov.lines.values():
            if linecov.is_reportable:
                lines_elem.append(_line_element(linecov))

        stats = filecov.stats

        class_name = fname.replace(".", "_")
        class_elem.set("name", class_name)
        class_elem.set(
            "sourcefilename", force_unix_separator(os.path.join(options.root, filename))
        )
        class_elem.append(_counter_element("LINE", stats.line))
        class_elem.append(_counter_element("BRANCH", stats.branch))

        package_data.classes_xml[class_name] = class_elem
        package_data.stats += stats

    for package_name in sorted(packages):
        package_data = packages[package_name]
        package_elem = etree.SubElement(root_elem, "package")
        for class_name in sorted(package_data.classes_xml):
            package_elem.append(package_data.classes_xml[class_name])
        package_elem.append(_counter_element("LINE", package_data.stats.line))
        package_elem.append(_counter_element("BRANCH", package_data.stats.branch))
        package_elem.set("name", package_name.replace("/", "."))

    stats = covdata.stats
    root_elem.append(_counter_element("LINE", stats.line))
    root_elem.append(_counter_element("BRANCH", stats.branch))

    with open_binary_for_writing(output_file, "jacoco.xml") as fh:
        fh.write(
            etree.tostring(
                root_elem,
                pretty_print=options.jacoco_pretty,
                encoding="UTF-8",
                xml_declaration=True,
                doctype="<!DOCTYPE coverage SYSTEM 'https://www.jacoco.org/jacoco/trunk/coverage/report.dtd'>",
            )
        )


@dataclass
class PackageData:
    """Class holding package information."""

    classes_xml: dict[str, etree._Element]
    stats: SummarizedStats


def _counter_element(element_type: str, stat: CoverageStat) -> etree._Element:
    """format a CoverageStat as a string in range 0.0 to 1.0 inclusive"""
    counter_elem = etree.Element("counter")
    counter_elem.set("type", element_type)
    counter_elem.set("missed", str(stat.total - stat.covered))
    counter_elem.set("covered", str(stat.covered))

    return counter_elem


def _line_element(linecov: LineCoverage) -> etree._Element:
    stat = linecov.branch_coverage()

    line_elem = etree.Element("line")
    line_elem.set("nr", str(linecov.lineno))

    if stat.total:
        line_elem.set("mb", str(stat.total - stat.covered))
        line_elem.set("cb", str(stat.covered))

    return line_elem
