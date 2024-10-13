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

# cspell:ignore addoption


def pytest_addoption(parser):  # pragma: no cover
    parser.addoption(
        "--generate_reference", action="store_true", help="Generate the reference"
    )
    parser.addoption(
        "--update_reference", action="store_true", help="Update the reference"
    )
    parser.addoption(
        "--archive_differences", action="store_true", help="Archive the different files"
    )
    parser.addoption(
        "--skip_clean", action="store_true", help="Skip the clean after the test"
    )
