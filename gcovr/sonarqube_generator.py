# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os

try:
    xrange
except NameError:
    xrange = range


#
# Produce an XML report in the Sonarqube generic coverage format
#
def print_sonarqube_report(covdata, options):
    root = "<?xml version=\"1.0\" ?>\n" + "<coverage version=\"1\">\n"
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

        filename = os.path.join(directory, fname).replace('\\', '/')
        fileNode = "<file path=\"" + filename + "\">\n"

        for lineno in sorted(data.lines):
            line_cov = data.lines[lineno]
            if not line_cov.is_covered and not line_cov.is_uncovered:
                continue

            attrLineNum = " lineNumber=\"" + str(lineno) + "\""
            attrCovered = " covered="
            if line_cov.is_covered:
                attrCovered += "\"true\""
            else:
                attrCovered += "\"false\""

            attrBranchesToCover = ""
            attrCoveredBranches = ""
            branches = line_cov.branches
            if branches:
                b_total, b_hits, coverage = line_cov.branch_coverage()
                attrBranchesToCover = " branchesToCover=\"" + str(b_total) + "\""
                attrCoveredBranches = " coveredBranches=\"" + str(b_hits) + "\""

            L =  "<lineToCover"
            L += attrBranchesToCover
            L += attrCovered
            L += attrCoveredBranches
            L += attrLineNum
            L += "/>\n"
            fileNode += L

        root += fileNode + "</file>\n"

    xmlString = root + "</coverage>\n"

    OUTPUT = open(options.sonarqube, 'w')
    OUTPUT.write(xmlString + '\n')
    OUTPUT.close()
