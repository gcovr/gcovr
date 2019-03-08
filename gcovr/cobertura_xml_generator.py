# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os
import sys
import time
from contextlib import contextmanager

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as etree
    LXML_AVAILABLE = False

from .version import __version__

try:
    xrange
except NameError:
    xrange = range


@contextmanager
def smart_open(filename=None):
    if filename and filename != '-':
        # files in write binary mode for UTF-8
        fh = open(filename, 'wb')
    elif (sys.version_info > (3, 0)):
        # python 3 wants stdout.buffer for binary output
        fh = sys.stdout.buffer
    else:
        # python2 doesn't care as much, no stdout.buffer
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()
#
# Produce an XML report in the Cobertura format
#


def print_xml_report(covdata, options):
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

    # impl = xml.dom.minidom.getDOMImplementation()
    # docType = impl.createDocumentType(
    #     "coverage", None,
    #     "http://cobertura.sourceforge.net/xml/coverage-04.dtd"
    # )
    # doc = impl.createDocument(None, "coverage", docType)
    # root = doc.documentElement
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
    # root.appendChild(sources)
    sources = etree.SubElement(root, "sources")

    # Generate the coverage output (on a per-package basis)
    # packageXml = doc.createElement("packages")
    # root.appendChild(packageXml)
    packageXml = etree.SubElement(root, "packages")
    packages = {}
    source_dirs = set()

    for f in sorted(covdata):
        data = covdata[f]
        directory = options.root_filter.sub('', f)
        if f.endswith(directory):
            src_path = f[:-1 * len(directory)]
            if len(src_path) > 0:
                while directory.startswith(os.path.sep):
                    src_path += os.path.sep
                    directory = directory[len(os.path.sep):]
                source_dirs.add(src_path)
        else:
            # Do no truncation if the filter does not start matching at
            # the beginning of the string
            directory = f
        directory, fname = os.path.split(directory)

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
        c.set("filename", os.path.join(directory, fname).replace('\\', '/'))
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
        package.set("name", packageName.replace(os.sep, '.'))
        package.set(
            "line-rate", str(packageData[2] / (1.0 * packageData[3] or 1.0))
        )
        package.set(
            "branch-rate", str(packageData[4] / (1.0 * packageData[5] or 1.0))
        )
        package.set("complexity", "0.0")

    # Populate the <sources> element: this is the root directory
    etree.SubElement(sources, "source").text = options.root.strip()

    with smart_open(options.output) as fh:
        if LXML_AVAILABLE:
            fh.write(
                etree.tostring(root,
                               pretty_print=options.prettyxml,
                               encoding="UTF-8",
                               xml_declaration=True,
                               doctype="<!DOCTYPE coverage SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-04.dtd'>"))
        else:
            fh.write(etree.tostring(root, encoding="UTF-8"))
