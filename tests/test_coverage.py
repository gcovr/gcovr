# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 7.2+main, a parsing and reporting tool for gcov.
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

from gcovr.coverage import (
    DirectoryCoverage,
)

import os
import pytest
import re


GCOVR_ISOLATED_TEST = os.getenv("GCOVR_ISOLATED_TEST") == "zkQEVaBpXF1i"


def fix_filename(filename: str) -> str:
    return filename.replace("\\", os.sep).replace("/", os.sep)


@pytest.mark.parametrize(
    "test_input,root_dir,expected",
    [
        ("/foo/bar/foobar.cpp", "/foo", "/foo/bar/"),
        ("/foo/bar/A/B.cpp", "/foo/bar", "/foo/bar/A/"),
        ("/foo/bar/A/B", "/foo/bar", "/foo/bar/A/"),
        ("/foo/bar", "/foo/bar", None),
        ("/A/bar.cpp", "/A", "/A/"),
        ("/A", "/A", None),
        ("C:\\foo\\bar\\A\\foobar.cpp", "C:/foo/bar", "C:/foo/bar/A/"),
        ("C:\\foo\\bar\\A", "C:/foo/bar", "C:/foo/bar/"),
    ],
)
def test_get_dirname(test_input, root_dir, expected, capsys) -> None:
    r"""Tests the _get_dirname function. Tests posix and Windows path cases."""
    root_filter = re.compile("^" + re.escape(fix_filename(root_dir) + os.sep))
    dirname = DirectoryCoverage._get_dirname(test_input, root_filter)
    if expected:
        expected = fix_filename(expected)
    assert dirname == expected

    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
