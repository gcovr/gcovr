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

import pytest
import typing


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.json
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test ignoring GCOV output errors."""

    gcovr_test_exec.run(
        "sh", "-c", "cat test.cpp | $CXX $CXXFLAGS -x c++ -c - -o test.o"
    )
    gcovr_test_exec.cxx_link(
        "testcase", gcovr_test_exec.cxx_compile("code.cpp"), "test.o"
    )

    gcovr_test_exec.run("./testcase")
    gcovr_args = [
        "--verbose",
        "--json-pretty",
        "--json=coverage.json",
    ]
    if not gcovr_test_exec.use_gcc_json_format():
        gcovr_args.insert(0, "--gcov-ignore-errors=no_working_dir_found")
    gcovr_test_exec.gcovr(*gcovr_args)
    gcovr_test_exec.compare_json()
