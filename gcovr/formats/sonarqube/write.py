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

from lxml import etree  # nosec # We only write XML files

from ...options import Options

from ...utils import open_binary_for_writing, presentable_filename
from ...coverage import CovData


def write_report(covdata: CovData, output_file: str, options: Options) -> None:
    """produce an XML report in the SonarQube generic coverage format"""

    root = etree.Element("coverage")
    root.set("version", "1")

    for f in sorted(covdata):
        data = covdata[f]
        filename = presentable_filename(f, root_filter=options.root_filter)

        fileNode = etree.Element("file")
        fileNode.set("path", filename)

        for lineno in sorted(data.lines):
            line_cov = data.lines[lineno]
            if not line_cov.is_covered and not line_cov.is_uncovered:
                continue

            L = etree.Element("lineToCover")
            L.set("lineNumber", str(lineno))
            if line_cov.is_covered:
                L.set("covered", "true")
            else:
                L.set("covered", "false")

            branches = line_cov.branches
            if branches:
                b = line_cov.branch_coverage()
                L.set("branchesToCover", str(b.total))
                L.set("coveredBranches", str(b.covered))

            fileNode.append(L)

        root.append(fileNode)

    with open_binary_for_writing(output_file, "sonarqube.xml") as fh:
        fh.write(etree.tostring(root, encoding="UTF-8", xml_declaration=True))
