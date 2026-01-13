# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import typing

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.json
def test_oos_1(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test out-of-source build and coverage."""
    build_dir = gcovr_test_exec.output_dir / "build"
    build_dir.mkdir()
    gcovr_test_exec.cxx_link(
        "build/testcase",
        gcovr_test_exec.cxx_compile("src/file1.cpp", target="build/file1.o"),
        gcovr_test_exec.cxx_compile("src/main.cpp", target="build/main.o"),
    )

    gcovr_test_exec.run("./build/testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()


@pytest.mark.json
def test_oos_2(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test out-of-source build and coverage."""
    build_dir = gcovr_test_exec.output_dir / "build"
    build_dir.mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile(
            "../src/file1.cpp", target="file1.o", cwd=build_dir
        ),
        gcovr_test_exec.cxx_compile("../src/main.cpp", target="main.o", cwd=build_dir),
        cwd=build_dir,
    )

    gcovr_test_exec.run("./build/testcase")
    gcovr_test_exec.gcovr(
        "-r",
        "../src",
        "--json-pretty",
        "--json",
        "../coverage.json",
        ".",
        cwd=build_dir,
    )
    gcovr_test_exec.compare_json()
