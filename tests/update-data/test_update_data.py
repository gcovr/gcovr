#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.8, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.8
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

from tests.conftest import IS_LINUX, GcovrExecFixture


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Merging is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.json
def test(gcovr_exec: "GcovrExecFixture") -> None:
    """
    A test that verifies CoverageData.update function.

    The same header will be included by 2 source files and
    shall report 100% coverage.
    """
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
        gcovr_exec.cc_compile("update-data.c"),
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr("--json-pretty", "--json", "coverage.json")
    gcovr_exec.compare_json()
