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

        file_node = etree.Element("file")
        file_node.set("path", filename)

        for lineno in sorted(data.lines):
            line_cov = data.lines[lineno]
            if not line_cov.is_covered and not line_cov.is_uncovered:
                continue

            line_node = etree.Element("lineToCover")
            line_node.set("lineNumber", str(lineno))
            if line_cov.is_covered:
                line_node.set("covered", "true")
            else:
                line_node.set("covered", "false")

            branches = line_cov.branches
            if branches:
                b = line_cov.branch_coverage()
                line_node.set("branchesToCover", str(b.total))
                line_node.set("coveredBranches", str(b.covered))

            file_node.append(line_node)

        root.append(file_node)

    with open_binary_for_writing(output_file, "sonarqube.xml") as fh:
        fh.write(etree.tostring(root, encoding="UTF-8", xml_declaration=True))
