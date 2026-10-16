#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.7+main, a parsing and reporting tool for gcov.
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
    from tests.conftest import GcovrExecFixture


@pytest.mark.parametrize(
    "sort",
    ["uncovered-percent", "uncovered-number"],
)
@pytest.mark.html
@pytest.mark.txt
def test(gcovr_exec: "GcovrExecFixture", sort: str) -> None:
    """Test excluding of functions."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("file1.cpp"),
        gcovr_exec.cxx_compile("file2.cpp"),
        gcovr_exec.cxx_compile("file3.cpp"),
        gcovr_exec.cxx_compile("file4.cpp"),
        gcovr_exec.cxx_compile("main.cpp"),
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        f"--sort={sort}",
        "--html=coverage.html",
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        f"--sort={sort}",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()
