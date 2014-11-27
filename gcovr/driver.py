#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# A report generator for gcov 3.4
#
# This routine generates a format that is similar to the format generated
# by the Python coverage.py module.  This code is similar to the
# data processing performed by lcov's geninfo command.  However, we
# don't worry about parsing the *.gcna files, and backwards compatibility for
# older versions of gcov is not supported.
#
# Outstanding issues
#   - verify that gcov 3.4 or newer is being used
#   - verify support for symbolic links
#
# gcovr is a FAST project.  For documentation, bug reporting, and
# updates, see http://gcovr.com/
#
#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
# _________________________________________________________________________
#
# $Revision$
# $Date$
#

import os
import re
import sys

from os.path import normpath

from gcovr.version import version_str
from gcovr.args import parse_arguments
from gcovr.data import get_coverage_data
from gcovr.prints.xml import print_xml_report
from gcovr.prints.html import print_html_report
from gcovr.prints.text import print_text_report, print_summary


##
## MAIN
##
def main(options, args):

    if options.version:
        sys.stdout.write(
            "gcovr %s\n"
            "\n"
            "Copyright (2013) Sandia Corporation. Under the terms of Contract\n"
            "DE-AC04-94AL85000 with Sandia Corporation, the U.S. Government\n"
            "retains certain rights in this software.\n"
            % (version_str(), )
        )
        sys.exit(0)

    if options.objdir:
        tmp = options.objdir.replace('/', os.sep).replace('\\', os.sep)
        while os.sep + os.sep in tmp:
            tmp = tmp.replace(os.sep + os.sep, os.sep)
        if normpath(options.objdir) != tmp:
            sys.stderr.write(
                "(WARNING) relative referencing in --object-directory.\n"
                "\tthis could cause strange errors when gcovr attempts to\n"
                "\tidentify the original gcc working directory.\n")
        if not os.path.exists(normpath(options.objdir)):
            sys.stderr.write(
                "(ERROR) Bad --object-directory option.\n"
                "\tThe specified directory does not exist.\n")
            sys.exit(1)
    #
    # Setup filters
    #
    for i in range(0, len(options.exclude)):
        options.exclude[i] = re.compile(options.exclude[i])

    options.root_filter = re.compile('')
    options.root_dir = os.path.normpath(os.getcwd())
    if options.root is not None:
        if not options.root:
            sys.stderr.write(
                "(ERROR) empty --root option.\n"
                "\tRoot specifies the path to the root "
                "directory of your project.\n"
                "\tThis option cannot be an empty string.\n"
            )
            sys.exit(1)
        options.root_dir = os.path.normcase(os.path.abspath(options.root))
        options.root_filter = re.compile(re.escape(options.root_dir + os.sep))
    else:
        options.root = "."

    for i in range(0, len(options.filter)):
        options.filter[i] = re.compile(options.filter[i])
    if len(options.filter) == 0:
        options.filter.append(options.root_filter)

    for i in range(0, len(options.gcov_exclude)):
        options.gcov_exclude[i] = re.compile(options.gcov_exclude[i])
    if options.gcov_filter is not None:
        options.gcov_filter = re.compile(options.gcov_filter)
    else:
        options.gcov_filter = re.compile('')

    #
    # Get coverage data
    #

    #
    # if the objdir is given i think it also should be used to get the coverage data
    #
    if options.objdir:
        paths = [options.objdir]
    else:
        paths = args
        if len(args) == 0:
            paths = [options.root]

    if options.verbose:
        if options.root is not None:
            sys.stdout.write("\noptions.root: "+options.root)
        if options.root_dir is not None:
            sys.stdout.write("\noptions.root_dir: "+options.root_dir)
        if options.objdir is not None:
            sys.stdout.write("\noptions.objdir: " + options.objdir)

    covdata = get_coverage_data(paths, options)

    #
    # Print report
    #
    if options.xml or options.prettyxml:
        print_xml_report(covdata, options)
    elif options.html:
        print_html_report(covdata, options)
    else:
        print_text_report(covdata, options)

    if options.print_summary:
        print_summary(covdata, options)


def main_():
    options, args = parse_arguments()
    main(options, args)

