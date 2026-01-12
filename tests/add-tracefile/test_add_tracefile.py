# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.5+main, a parsing and reporting tool for gcov.
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

import pytest
import typing


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.json
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test merging of tracefiles."""
    common_objects = [
        gcovr_test_exec.cxx_compile("foo.cpp"),
        gcovr_test_exec.cxx_compile("bar.cpp"),
    ]
    gcovr_test_exec.cxx_link(
        "testcase_foo",
        gcovr_test_exec.cxx_compile("main.cpp", target="main_foo.o", options=["-DFOO"]),
        *common_objects,
    )
    gcovr_test_exec.cxx_link(
        "testcase_bar",
        gcovr_test_exec.cxx_compile("main.cpp", target="main_bar.o", options=["-DBAR"]),
        *common_objects,
    )

    gcovr_test_exec.run("./testcase_foo")
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--json-pretty", "--json", "coverage_foo.json"
    )

    gcovr_test_exec.run("./testcase_bar")
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--json-pretty", "--json", "coverage_bar.json"
    )

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage_*.json",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
