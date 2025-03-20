# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
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

from ...data_model.container import CoverageContainer
from ...options import Options
from ...utils import write_xml_output


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce an XML report in the SonarQube generic coverage format"""

    root_elem = etree.Element("coverage")
    root_elem.set("version", "1")

    for fname in sorted(covdata):
        filecov = covdata[fname]
        filename = filecov.presentable_filename(options.root_filter)

        file_node = etree.Element("file")
        file_node.set("path", filename)

        for linecov in filecov.lines.values():
            if linecov.is_reportable:
                line_node = etree.Element("lineToCover")
                line_node.set("lineNumber", str(linecov.lineno))
                line_node.set("covered", "true" if linecov.is_covered else "false")

                if linecov.branches:
                    stat = linecov.branch_coverage()
                    line_node.set("branchesToCover", str(stat.total))
                    line_node.set("coveredBranches", str(stat.covered))

                file_node.append(line_node)

        root_elem.append(file_node)

    write_xml_output(
        root_elem,
        pretty=False,
        filename=output_file,
        default_filename="sonarqube.xml",
        doctype="<!DOCTYPE coverage SYSTEM 'https://www.jacoco.org/jacoco/trunk/coverage/report.dtd'>",
    )
