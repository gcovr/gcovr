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
    packageXml = etree.SubElement(root, "packages")
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
        # The Cobertura DTD requires a methods section, which isn't
        # trivial to get from gcov (so we will leave it blank)
        methods = etree.SubElement(c, "methods")
        for functioncov in data.functions.values():
            if functioncov.name is not None:
                filtered_filecov = data.filter_for_function(functioncov)
                function_stats = SummarizedStats.from_file(filtered_filecov)
                name = functioncov.demangled_name
                if "(" in name:
                    name = name.split("(", maxsplit=1)[0]
                    signature = functioncov.demangled_name[len(name) :]
                else:
                    signature = "()"
                method = etree.SubElement(methods, "method")
                method.set("name", name)
                method.set("signature", signature)
                method.set("line-rate", _rate(function_stats.line))
                method.set("branch-rate", _rate(function_stats.branch))
                method.set("complexity", "0.0")
                lines = etree.SubElement(method, "lines")
                for line_cov in filtered_filecov.lines.values():
                    if line_cov.is_reportable:
                        lines.append(_line_element(line_cov))

        lines = etree.SubElement(c, "lines")

        # TODO should use FileCoverage.branch_coverage() calculation
        class_branch = CoverageStat.new_empty()
        for line_cov in data.lines.values():
            if line_cov.is_reportable:
                b = line_cov.branch_coverage()
                if b.total:
                    class_branch += b

                lines.append(_line_element(line_cov))

        stats = SummarizedStats.from_file(data)

        className = fname.replace(".", "_")
        c.set("name", className)
        c.set("filename", filename)
        c.set("line-rate", _rate(stats.line))
        c.set("branch-rate", _rate(class_branch))
        c.set("complexity", "0.0")

        package.classes_xml[className] = c
        package.line += stats.line
        package.branch += class_branch

    for packageName in sorted(packages):
        packageData = packages[packageName]
        package = etree.Element("package")
        packageXml.append(package)
        classes = etree.SubElement(package, "classes")
        for className in sorted(packageData.classes_xml):
            classes.append(packageData.classes_xml[className])
        package.set("name", packageName.replace("/", "."))
        package.set("line-rate", _rate(packageData.line))
        package.set("branch-rate", _rate(packageData.branch))
        package.set("complexity", "0.0")

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


def _line_element(line: LineCoverage) -> etree.Element:
    branch = line.branch_coverage()

    elem = etree.Element("line")
    elem.set("number", str(line.lineno))
    elem.set("hits", str(line.count))

    if not branch.total:
        elem.set("branch", "false")
    elif branch.percent is None:
        raise AssertionError("Percent coverage must not be 'None'.")
    else:
        elem.set("branch", "true")
        elem.set(
            "condition-coverage",
            f"{int(branch.percent)}% ({branch.covered}/{branch.total})",
        )
        elem.append(_conditions_element(branch))

    return elem


def _conditions_element(branch: CoverageStat) -> etree.Element:
    elem = etree.Element("conditions")
    elem.append(_condition_element(branch))
    return elem


def _condition_element(branch: CoverageStat) -> etree.Element:
    coverage = branch.percent
    if coverage is None:
        raise AssertionError("Percent coverage must not be 'None'.")

    elem = etree.Element("condition")
    elem.set("number", "0")
    elem.set("type", "jump")
    elem.set("coverage", f"{int(coverage)}%")
    return elem
