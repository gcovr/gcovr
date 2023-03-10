# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0+master, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from ..coverage import (
    CovData_subdirectories,
    DirectoryCoverage,
    FileCoverage,
    LineCoverage,
)

import os
import pytest
import re


GCOVR_ISOLATED_TEST = os.getenv("GCOVR_ISOLATED_TEST") == "zkQEVaBpXF1i"


def fix_filename(filename: str) -> str:
    return filename.replace("\\", os.sep).replace("/", os.sep)


def compile_filter(root_dir: str) -> re.Pattern:
    return re.compile("^" + re.escape(fix_filename(root_dir) + os.sep))


@pytest.mark.parametrize(
    "test_input,root_dir,expected",
    [
        ("/foo/bar/foobar.cpp", "/foo", "/foo/bar"),
        ("/foo/bar/A/B.cpp", "/foo/bar", "/foo/bar/A"),
        ("/foo/bar/A/B", "/foo/bar", "/foo/bar/A"),
        ("/foo/bar", "/foo/bar", None),
        ("/A/bar.cpp", "/A", "/A"),
        ("/A", "/A", None),
        ("C:\\foo\\bar\\A\\foobar.cpp", "C:/foo/bar", "C:/foo/bar/A"),
        ("C:\\foo\\bar\\A", "C:/foo/bar", "C:/foo/bar"),
    ],
)
def test_directory_key(test_input, root_dir, expected, capsys) -> None:
    r"""Tests the directory_key() function. Tests posix and Windows path cases."""
    root_filter = compile_filter(root_dir)
    key = DirectoryCoverage.directory_key(test_input, root_filter)
    if expected:
        expected = fix_filename(expected)
    assert key == expected

    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_directory_line_coverage() -> None:
    r"""Tests line_coverage and branch_coverage() that can be used for sort_coverage()."""
    dircov = DirectoryCoverage.new_empty()
    dircov.dirname = "/foo/bar/A"
    dircov.parent_key = "/foo/bar"
    dircov.stats.line.covered = 50
    dircov.stats.line.total = 100
    dircov.stats.branch.covered = 25
    dircov.stats.branch.total = 40

    cov = dircov.line_coverage()
    assert cov.covered == 50
    assert cov.total == 100

    cov = dircov.branch_coverage()
    assert cov.covered == 25
    assert cov.total == 40


def add_file_to_directory(
    subdirs: CovData_subdirectories,
    fname: str,
    root_dir: str,
    cov_lines: int,
    total_lines: int,
) -> None:
    r"""helpher function to add a file to a tree structure."""
    root_filter = compile_filter(root_dir)
    assert cov_lines <= total_lines
    newfile = FileCoverage(fname)
    for line in range(total_lines):
        newfile.lines[line + 1] = LineCoverage(
            line + 1,
            count=(True if line < cov_lines else False),
            excluded=False,
        )
    DirectoryCoverage.add_directory_coverage(subdirs, root_filter, newfile)


def test_directory_add_file() -> None:
    r"""Tests the addition of files and their aggregation of statistics."""
    subdirs = dict()

    root_dir = fix_filename("/foo/bar")
    add_file_to_directory(subdirs, "/foo/bar/main.cpp", root_dir, 20, 50)
    assert len(subdirs) == 1
    add_file_to_directory(subdirs, "/foo/bar/helper.cpp", root_dir, 10, 50)
    assert len(subdirs) == 1

    dircov = subdirs[root_dir]

    assert len(dircov.children) == 2
    linecov = dircov.line_coverage()

    assert linecov.covered == 30
    assert linecov.total == 100


def test_directory_root() -> None:
    r"""Tests the root_directory() function for DirectoryCoverage."""
    subdirs = dict()
    root_dir = fix_filename("/foo/bar")
    root_filter = compile_filter(root_dir)

    assert DirectoryCoverage.directory_root(subdirs, root_filter) == os.sep

    add_file_to_directory(subdirs, "/foo/bar/main.cpp", root_dir, 20, 50)
    add_file_to_directory(subdirs, "/foo/bar/A/B/C/D/E.cpp", root_dir, 10, 50)
    assert DirectoryCoverage.directory_root(subdirs, root_filter) == root_dir


def test_directory_collapse() -> None:
    r"""Tests the collapse of subdirectories with a single entry."""
    subdirs = dict()

    root_dir = "/foo/bar"
    add_file_to_directory(subdirs, "/foo/bar/main.cpp", root_dir, 20, 50)
    assert len(subdirs) == 1
    add_file_to_directory(subdirs, "/foo/bar/A/B/C/D/E.cpp", root_dir, 10, 50)
    assert len(subdirs) == 5
    root_filter = compile_filter(root_dir)
    DirectoryCoverage.collapse_subdirectories(subdirs, root_filter)
    assert len(subdirs) == 1

    dircov = subdirs[fix_filename(root_dir)]

    assert len(dircov.children) == 2
    linecov = dircov.line_coverage()

    assert linecov.covered == 30
    assert linecov.total == 100
