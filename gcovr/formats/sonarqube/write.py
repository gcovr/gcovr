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

    for fname in sorted(covdata):
        filecov = covdata[fname]
        filename = presentable_filename(fname, root_filter=options.root_filter)

        file_elem = etree.Element("file")
        file_elem.set("path", filename)

        for lineno in sorted(filecov.lines):
            linecov = filecov.lines[lineno]
            if linecov.is_reportable:
                line_elem = etree.Element("lineToCover")
                line_elem.set("lineNumber", str(lineno))
                line_elem.set("covered", "true" if linecov.is_covered else "false")

                if linecov.branches:
                    stat = linecov.branch_coverage()
                    line_elem.set("branchesToCover", str(stat.total))
                    line_elem.set("coveredBranches", str(stat.covered))

                file_elem.append(line_elem)

        root.append(file_elem)

    with open_binary_for_writing(output_file, "sonarqube.xml") as fh:
        fh.write(etree.tostring(root, encoding="UTF-8", xml_declaration=True))
