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

from dataclasses import dataclass
import os
from lxml import etree  # nosec # We only write XML files

from ...options import Options

from ...utils import (
    force_unix_separator,
    get_version_for_report,
    open_binary_for_writing,
    presentable_filename,
)
from ...coverage import CoverageContainer, CoverageStat, LineCoverage, SummarizedStats


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce an XML report in the Cobertura format"""

    stats = covdata.stats

    root_elem = etree.Element("coverage")
    root_elem.set("line-rate", _rate(stats.line))
    root_elem.set("branch-rate", _rate(stats.branch))
    root_elem.set("lines-covered", str(stats.line.covered))
    root_elem.set("lines-valid", str(stats.line.total))
    root_elem.set("branches-covered", str(stats.branch.covered))
    root_elem.set("branches-valid", str(stats.branch.total))
    root_elem.set("complexity", "0.0")
    root_elem.set("timestamp", str(int(options.timestamp.timestamp())))
    root_elem.set("version", f"gcovr {get_version_for_report()}")

    # Generate the <sources> element: this is either the root directory
    # (specified by --root), or the CWD.
    sources = etree.SubElement(root_elem, "sources")

    # Generate the coverage output (on a per-package basis)
    packages_elem = etree.SubElement(root_elem, "packages")
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
        # The Cobertura DTD requires a methods section, which isn't
        # trivial to get from gcov (so we will leave it blank)
        methods_elem = etree.SubElement(class_elem, "methods")
        for functioncov in filecov.functions.values():
            if functioncov.name is not None:
                filtered_filecov = filecov.filter_for_function(functioncov)
                function_stats = filtered_filecov.stats
                name = functioncov.demangled_name
                if "(" in name:
                    name = name.split("(", maxsplit=1)[0]
                    signature = functioncov.demangled_name[len(name) :]
                else:
                    signature = "()"
                method_elem = etree.SubElement(methods_elem, "method")
                method_elem.set("name", name)
                method_elem.set("signature", signature)
                method_elem.set("line-rate", _rate(function_stats.line))
                method_elem.set("branch-rate", _rate(function_stats.branch))
                method_elem.set("complexity", "0.0")
                lines_elem = etree.SubElement(method_elem, "lines")
                for linecov in filtered_filecov.lines.values():
                    if linecov.is_reportable:
                        lines_elem.append(_line_element(linecov))

        lines_elem = etree.SubElement(class_elem, "lines")

        for linecov in filecov.lines.values():
            if linecov.is_reportable:
                lines_elem.append(_line_element(linecov))

        stats = filecov.stats

        class_name = fname.replace(".", "_")
        class_elem.set("name", class_name)
        class_elem.set("filename", filename)
        class_elem.set("line-rate", _rate(stats.line))
        class_elem.set("branch-rate", _rate(stats.branch))
        class_elem.set("complexity", "0.0")

        package_data.classes_xml[class_name] = class_elem
        package_data.stats += stats

    for package_name in sorted(packages):
        package_data = packages[package_name]
        package_elem = etree.SubElement(packages_elem, "package")
        classes_elem = etree.SubElement(package_elem, "classes")
        for class_name in sorted(package_data.classes_xml):
            classes_elem.append(package_data.classes_xml[class_name])
        package_elem.set("name", package_name.replace("/", "."))
        package_elem.set("line-rate", _rate(package_data.stats.line))
        package_elem.set("branch-rate", _rate(package_data.stats.branch))
        package_elem.set("complexity", "0.0")

    # Populate the <sources> element: this is the root directory
    etree.SubElement(sources, "source").text = force_unix_separator(
        os.path.abspath(options.root)
    )

    with open_binary_for_writing(output_file, "cobertura.xml") as fh:
        fh.write(
            etree.tostring(
                root_elem,
                pretty_print=options.cobertura_pretty,
                encoding="UTF-8",
                xml_declaration=True,
                doctype="<!DOCTYPE coverage SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-04.dtd'>",
            )
        )


@dataclass
class PackageData:
    """Data class holding the package data"""

    classes_xml: dict[str, etree._Element]
    stats: SummarizedStats


def _rate(stat: CoverageStat) -> str:
    """format a CoverageStat as a string in range 0.0 to 1.0 inclusive"""
    total = stat.total
    covered = stat.covered
    if not total:
        return "1.0"
    return str(covered / total)


def _line_element(linecov: LineCoverage) -> etree._Element:
    stat = linecov.branch_coverage()

    elem = etree.Element("line")
    elem.set("number", str(linecov.lineno))
    elem.set("hits", str(linecov.count))

    if not stat.total:
        elem.set("branch", "false")
    elif stat.percent is None:
        raise AssertionError("Percent coverage must not be 'None'.")
    else:
        elem.set("branch", "true")
        elem.set(
            "condition-coverage",
            f"{int(stat.percent)}% ({stat.covered}/{stat.total})",
        )
        elem.append(_conditions_element(stat))

    return elem


def _conditions_element(branch: CoverageStat) -> etree._Element:
    elem = etree.Element("conditions")
    elem.append(_condition_element(branch))
    return elem


def _condition_element(branch: CoverageStat) -> etree._Element:
    coverage = branch.percent
    if coverage is None:
        raise AssertionError("Percent coverage must not be 'None'.")

    elem = etree.Element("condition")
    elem.set("number", "0")
    elem.set("type", "jump")
    elem.set("coverage", f"{int(coverage)}%")
    return elem
