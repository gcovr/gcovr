# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import time

from lxml import etree

from ..version import __version__
from ..utils import open_binary_for_writing, presentable_filename


def print_xml_report(covdata, output_file, options):
    """produce an XML report in the Cobertura format"""
    branchTotal = 0
    branchCovered = 0
    lineTotal = 0
    lineCovered = 0

    for key in covdata.keys():
        (total, covered, _) = covdata[key].branch_coverage()
        branchTotal += total
        branchCovered += covered

    for key in covdata.keys():
        (total, covered, _) = covdata[key].line_coverage()
        lineTotal += total
        lineCovered += covered

    root = etree.Element("coverage")
    root.set(
        "line-rate", lineTotal == 0 and '0.0'
        or str(float(lineCovered) / lineTotal)
    )
    root.set(
        "branch-rate", branchTotal == 0 and '0.0'
        or str(float(branchCovered) / branchTotal)
    )
    root.set(
        "lines-covered", str(lineCovered)
    )
    root.set(
        "lines-valid", str(lineTotal)
    )
    root.set(
        "branches-covered", str(branchCovered)
    )
    root.set(
        "branches-valid", str(branchTotal)
    )
    root.set(
        "complexity", "0.0"
    )
    root.set(
        "timestamp", str(int(time.time()))
    )
    root.set(
        "version", "gcovr %s" % (__version__,)
    )

    # Generate the <sources> element: this is either the root directory
    # (specified by --root), or the CWD.
    # sources = doc.createElement("sources")
    sources = etree.SubElement(root, "sources")

    # Generate the coverage output (on a per-package basis)
    # packageXml = doc.createElement("packages")
    packageXml = etree.SubElement(root, "packages")
    packages = {}

    for f in sorted(covdata):
        data = covdata[f]
        filename = presentable_filename(f, root_filter=options.root_filter)
        if '/' in filename:
            directory, fname = filename.rsplit('/', 1)
        else:
            directory, fname = '', filename

        package = packages.setdefault(
            directory, [etree.Element("package"), {}, 0, 0, 0, 0]
        )
        c = etree.Element("class")
        # The Cobertura DTD requires a methods section, which isn't
        # trivial to get from gcov (so we will leave it blank)
        etree.SubElement(c, "methods")
        lines = etree.SubElement(c, "lines")

        class_lines = 0
        class_hits = 0
        class_branches = 0
        class_branch_hits = 0
        for lineno in sorted(data.lines):
            line_cov = data.lines[lineno]
            if line_cov.is_covered or line_cov.is_uncovered:
                class_lines += 1
            else:
                continue
            if line_cov.is_covered:
                class_hits += 1
            hits = line_cov.count
            L = etree.Element("line")
            L.set("number", str(lineno))
            L.set("hits", str(hits))
            branches = line_cov.branches
            if not branches:
                L.set("branch", "false")
            else:
                b_total, b_hits, coverage = line_cov.branch_coverage()
                L.set("branch", "true")
                L.set(
                    "condition-coverage",
                    "{}% ({}/{})".format(int(coverage), b_hits, b_total)
                )
                cond = etree.Element('condition')
                cond.set("number", "0")
                cond.set("type", "jump")
                cond.set("coverage", "{}%".format(int(coverage)))
                class_branch_hits += b_hits
                class_branches += float(len(branches))
                conditions = etree.Element("conditions")
                conditions.append(cond)
                L.append(conditions)

            lines.append(L)

        className = fname.replace('.', '_')
        c.set("name", className)
        c.set("filename", filename)
        c.set(
            "line-rate",
            str(class_hits / (1.0 * class_lines or 1.0))
        )
        c.set(
            "branch-rate",
            str(class_branch_hits / (1.0 * class_branches or 1.0))
        )
        c.set("complexity", "0.0")

        package[1][className] = c
        package[2] += class_hits
        package[3] += class_lines
        package[4] += class_branch_hits
        package[5] += class_branches

    keys = list(packages.keys())
    keys.sort()
    for packageName in keys:
        packageData = packages[packageName]
        package = packageData[0]
        packageXml.append(package)
        classes = etree.SubElement(package, "classes")
        classNames = list(packageData[1].keys())
        classNames.sort()
        for className in classNames:
            classes.append(packageData[1][className])
        package.set("name", packageName.replace('/', '.'))
        package.set(
            "line-rate", str(packageData[2] / (1.0 * packageData[3] or 1.0))
        )
        package.set(
            "branch-rate", str(packageData[4] / (1.0 * packageData[5] or 1.0))
        )
        package.set("complexity", "0.0")

    # Populate the <sources> element: this is the root directory
    etree.SubElement(sources, "source").text = options.root.strip()

    with open_binary_for_writing(output_file, 'coverage.xml') as fh:
        fh.write(
            etree.tostring(root,
                           pretty_print=options.prettyxml,
                           encoding="UTF-8",
                           xml_declaration=True,
                           doctype="<!DOCTYPE coverage SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-04.dtd'>"))
