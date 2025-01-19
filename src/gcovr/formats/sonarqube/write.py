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

from lxml import etree  # nosec # We only write XML files

from ...options import Options

from ...utils import open_binary_for_writing, presentable_filename
from ...coverage import CoverageContainer


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce an XML report in the SonarQube generic coverage format"""

    root = etree.Element("coverage")
    root.set("version", "1")

    for f in sorted(covdata):
        data = covdata[f]
        filename = presentable_filename(f, root_filter=options.root_filter)

        file_node = etree.Element("file")
        file_node.set("path", filename)

        for lineno, linecov in data.lines.items():
            if linecov.is_reportable:
                line_node = etree.Element("lineToCover")
                line_node.set("lineNumber", str(lineno))
                line_node.set("covered", "true" if linecov.is_covered else "false")

                if linecov.branches:
                    stat = linecov.branch_coverage()
                    line_node.set("branchesToCover", str(stat.total))
                    line_node.set("coveredBranches", str(stat.covered))

                file_node.append(line_node)

        root.append(file_node)

    with open_binary_for_writing(output_file, "sonarqube.xml") as fh:
        fh.write(etree.tostring(root, encoding="UTF-8", xml_declaration=True))
