# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2019 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os
from lxml import etree

from .utils import open_binary_for_writing


def print_sonarqube_report(covdata, options):
    """produce an XML report in the Sonarqube generic coverage format"""

    root = etree.Element("coverage")
    root.set("version", "1")
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

        fileNode = etree.Element("file")

        filename = os.path.join(directory, fname).replace('\\', '/')
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
                b_total, b_hits, coverage = line_cov.branch_coverage()
                L.set("branchesToCover", str(b_total))
                L.set("coveredBranches", str(b_hits))

            fileNode.append(L)

        root.append(fileNode)

    with open_binary_for_writing(options.sonarqube) as fh:
        fh.write(
            etree.tostring(root,
                           encoding="UTF-8",
                           xml_declaration=True))
