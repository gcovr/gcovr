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

import typing
from pathlib import Path

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture


@pytest.mark.html
@pytest.mark.json
def test(gcovr_exec: "GcovrExecFixture") -> None:
    """Test call coverage."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.c"),
    )

    gcovr_exec.run("./testcase")
    first_json = Path("first.json")
    gcovr_exec.gcovr("--calls", "--json", first_json)

    gcovr_exec.run("./testcase")
    second_json = Path("second.json")
    gcovr_exec.gcovr("--calls", "--json", second_json)

    gcovr_exec.gcovr(
        "--json-add-tracefile",
        first_json,
        "--json-add-tracefile",
        second_json,
        "--json=coverage.json",
    )
    gcovr_exec.compare_json()

    gcovr_exec.gcovr(
        "--calls",
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_exec.compare_html()
