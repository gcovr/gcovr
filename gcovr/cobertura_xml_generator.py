# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os
import sys
import time
import xml.dom.minidom

from .version import version_str

try:
    xrange
except NameError:
    xrange = range


#
# Produce an XML report in the Cobertura format
#
def print_xml_report(covdata, options):
    branchTotal = 0
    branchCovered = 0
    lineTotal = 0
    lineCovered = 0

    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(show_branch=True)
        branchTotal += total
        branchCovered += covered

    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(show_branch=False)
        lineTotal += total
        lineCovered += covered

    impl = xml.dom.minidom.getDOMImplementation()
    docType = impl.createDocumentType(
        "coverage", None,
        "http://cobertura.sourceforge.net/xml/coverage-04.dtd"
    )
    doc = impl.createDocument(None, "coverage", docType)
    root = doc.documentElement
    root.setAttribute(
        "line-rate", lineTotal == 0 and '0.0' or
        str(float(lineCovered) / lineTotal)
    )
    root.setAttribute(
        "branch-rate", branchTotal == 0 and '0.0' or
        str(float(branchCovered) / branchTotal)
    )
    root.setAttribute(
        "lines-covered", str(lineCovered)
    )
    root.setAttribute(
        "lines-valid", str(lineTotal)
    )
    root.setAttribute(
        "branches-covered", str(branchCovered)
    )
    root.setAttribute(
        "branches-valid", str(branchTotal)
    )
    root.setAttribute(
        "complexity", "0.0"
    )
    root.setAttribute(
        "timestamp", str(int(time.time()))
    )
    root.setAttribute(
        "version", "gcovr %s" % (version_str(),)
    )

    # Generate the <sources> element: this is either the root directory
    # (specified by --root), or the CWD.
    sources = doc.createElement("sources")
    root.appendChild(sources)

    # Generate the coverage output (on a per-package basis)
    packageXml = doc.createElement("packages")
    root.appendChild(packageXml)
    packages = {}
    source_dirs = set()

    keys = list(covdata.keys())
    keys.sort()
    for f in keys:
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
            directory, [doc.createElement("package"), {}, 0, 0, 0, 0]
        )
        c = doc.createElement("class")
        # The Cobertura DTD requires a methods section, which isn't
        # trivial to get from gcov (so we will leave it blank)
        c.appendChild(doc.createElement("methods"))
        lines = doc.createElement("lines")
        c.appendChild(lines)

        class_lines = 0
        class_hits = 0
        class_branches = 0
        class_branch_hits = 0
        for line in sorted(data.all_lines):
            hits = data.covered.get(line, 0)
            class_lines += 1
            if hits > 0:
                class_hits += 1
            L = doc.createElement("line")
            L.setAttribute("number", str(line))
            L.setAttribute("hits", str(hits))
            branches = data.branches.get(line)
            if branches is None:
                L.setAttribute("branch", "false")
            else:
                b_hits = 0
                for v in branches.values():
                    if v > 0:
                        b_hits += 1
                coverage = 100 * b_hits / len(branches)
                L.setAttribute("branch", "true")
                L.setAttribute(
                    "condition-coverage",
                    "%i%% (%i/%i)" % (coverage, b_hits, len(branches))
                )
                cond = doc.createElement('condition')
                cond.setAttribute("number", "0")
                cond.setAttribute("type", "jump")
                cond.setAttribute("coverage", "%i%%" % (coverage))
                class_branch_hits += b_hits
                class_branches += float(len(branches))
                conditions = doc.createElement("conditions")
                conditions.appendChild(cond)
                L.appendChild(conditions)

            lines.appendChild(L)

        className = fname.replace('.', '_')
        c.setAttribute("name", className)
        c.setAttribute("filename", os.path.join(directory, fname).replace('\\', '/'))
        c.setAttribute(
            "line-rate",
            str(class_hits / (1.0 * class_lines or 1.0))
        )
        c.setAttribute(
            "branch-rate",
            str(class_branch_hits / (1.0 * class_branches or 1.0))
        )
        c.setAttribute("complexity", "0.0")

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
        packageXml.appendChild(package)
        classes = doc.createElement("classes")
        package.appendChild(classes)
        classNames = list(packageData[1].keys())
        classNames.sort()
        for className in classNames:
            classes.appendChild(packageData[1][className])
        package.setAttribute("name", packageName.replace(os.sep, '.'))
        package.setAttribute(
            "line-rate", str(packageData[2] / (1.0 * packageData[3] or 1.0))
        )
        package.setAttribute(
            "branch-rate", str(packageData[4] / (1.0 * packageData[5] or 1.0))
        )
        package.setAttribute("complexity", "0.0")

    # Populate the <sources> element: this is the root directory
    source = doc.createElement("source")
    source.appendChild(doc.createTextNode(options.root.strip()))
    sources.appendChild(source)

    if options.prettyxml:
        import textwrap
        lines = doc.toprettyxml(" ").split('\n')
        for i in xrange(len(lines)):
            n = 0
            while n < len(lines[i]) and lines[i][n] == " ":
                n += 1
            lines[i] = "\n".join(textwrap.wrap(
                lines[i], 78,
                break_long_words=False,
                break_on_hyphens=False,
                subsequent_indent=" " + n * " "
            ))
        xmlString = "\n".join(lines)
        # print textwrap.wrap(doc.toprettyxml(" "), 80)
    else:
        xmlString = doc.toprettyxml(indent="")
    if options.output is None:
        sys.stdout.write(xmlString + '\n')
    else:
        OUTPUT = open(options.output, 'w')
        OUTPUT.write(xmlString + '\n')
        OUTPUT.close()
