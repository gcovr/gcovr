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

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from lxml import etree  # nosec # We only write XML files

from ...options import Options

from ...version import __version__
from ...utils import force_unix_separator, open_binary_for_writing, presentable_filename
from ...coverage import CovData, CoverageStat, LineCoverage, SummarizedStats


def write_report(covdata: CovData, output_file: str, options: Options) -> None:
    """produce an XML report in the Cobertura format"""

    stats = SummarizedStats.from_covdata(covdata)

    root = etree.Element("coverage")
    root.set("line-rate", _rate(stats.line))
    root.set("branch-rate", _rate(stats.branch))
    root.set("lines-covered", str(stats.line.covered))
    root.set("lines-valid", str(stats.line.total))
    root.set("branches-covered", str(stats.branch.covered))
    root.set("branches-valid", str(stats.branch.total))
    root.set("complexity", "0.0")
    root.set("timestamp", str(int(options.timestamp.timestamp())))
    root.set("version", f"gcovr {__version__}")

    # Generate the <sources> element: this is either the root directory
    # (specified by --root), or the CWD.
    sources = etree.SubElement(root, "sources")

    # Generate the coverage output (on a per-package basis)
    package_xml = etree.SubElement(root, "packages")
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
        # The Cobertura DTD requires a methods section, which isn't
        # trivial to get from gcov (so we will leave it blank)
        methods_elem = etree.SubElement(class_elem, "methods")
        for functioncov in filecov.functions.values():
            if functioncov.name is not None:
                filtered_filecov = filecov.filter_for_function(functioncov)
                function_stats = SummarizedStats.from_file(filtered_filecov)
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
                lines = etree.SubElement(method_elem, "lines")
                for linecov in filtered_filecov.lines.values():
                    if linecov.is_reportable:
                        lines.append(_line_element(linecov))

        lines = etree.SubElement(class_elem, "lines")

        for linecov in filecov.lines.values():
            if linecov.is_reportable:
                lines.append(_line_element(linecov))

        stats = SummarizedStats.from_file(filecov)

        class_name = fname.replace(".", "_")
        class_elem.set("name", class_name)
        class_elem.set("filename", filename)
        class_elem.set("line-rate", _rate(stats.line))
        class_elem.set("branch-rate", _rate(stats.branch))
        class_elem.set("complexity", "0.0")

        package.classes_xml[class_name] = class_elem
        package.line += stats.line
        package.branch += stats.branch

    for package_name in sorted(packages):
        package_data = packages[package_name]
        package_elem = etree.Element("package")
        package_xml.append(package_elem)
        classes = etree.SubElement(package_elem, "classes")
        for class_name in sorted(package_data.classes_xml):
            classes.append(package_data.classes_xml[class_name])
        package_elem.set("name", package_name.replace("/", "."))
        package_elem.set("line-rate", _rate(package_data.line))
        package_elem.set("branch-rate", _rate(package_data.branch))
        package_elem.set("complexity", "0.0")

    # Populate the <sources> element: this is the root directory
    etree.SubElement(sources, "source").text = force_unix_separator(
        options.root.strip()
    )

    with open_binary_for_writing(output_file, "cobertura.xml") as fh:
        fh.write(
            etree.tostring(
                root,
                pretty_print=options.cobertura_pretty,
                encoding="UTF-8",
                xml_declaration=True,
                doctype="<!DOCTYPE coverage SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-04.dtd'>",
            )
        )


@dataclass
class PackageData:
    classes_xml: Dict[str, etree.Element]
    line: CoverageStat
    branch: CoverageStat


def _rate(stat: CoverageStat) -> str:
    """format a CoverageStat as a string in range 0.0 to 1.0 inclusive"""
    total = stat.total
    covered = stat.covered
    if not total:
        return "1.0"
    return str(covered / total)


def _line_element(linecov: LineCoverage) -> etree.Element:
    stat = linecov.branch_coverage()

    line_elem = etree.Element("line")
    line_elem.set("number", str(linecov.lineno))
    line_elem.set("hits", str(linecov.count))

    if not stat.total:
        line_elem.set("branch", "false")
    elif stat.percent is None:
        raise AssertionError("Percent coverage must not be 'None'.")
    else:
        line_elem.set("branch", "true")
        line_elem.set(
            "condition-coverage",
            f"{int(stat.percent)}% ({stat.covered}/{stat.total})",
        )
        line_elem.append(_conditions_element(stat))

    return line_elem


def _conditions_element(branch: CoverageStat) -> etree.Element:
    conditions_elem = etree.Element("conditions")
    conditions_elem.append(_condition_element(branch))
    return conditions_elem


def _condition_element(branch: CoverageStat) -> etree.Element:
    coverage = branch.percent
    if coverage is None:
        raise AssertionError("Percent coverage must not be 'None'.")

    condition_elem = etree.Element("condition")
    condition_elem.set("number", "0")
    condition_elem.set("type", "jump")
    condition_elem.set("coverage", f"{int(coverage)}%")
    return condition_elem
