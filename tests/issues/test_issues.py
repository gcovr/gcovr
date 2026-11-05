#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.8+main, a parsing and reporting tool for gcov.
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

from tests.conftest import (
    IS_LINUX,
    USE_PROFDATA_POSSIBLE,
)

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Parsing of decision is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.json
@pytest.mark.parametrize(
    "input_format",
    ["gcov", "llvm"] if USE_PROFDATA_POSSIBLE else ["gcov"],
)
def test_issue_679(
    gcovr_exec: "GcovrExecFixture",
    input_format: str,
) -> None:
    """Test of decision parsing."""
    gcovr_exec.use_llvm_profdata = input_format == "llvm"
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        *(["--llvm-cov-binary=./testcase"] if gcovr_exec.use_llvm_profdata else []),
        "--keep-intermediate-files",
        "--verbose",
        "--decisions",
        "--json-pretty",
        "--json=coverage.json",
        use_main=not gcovr_exec.use_llvm_profdata,
    )
    gcovr_exec.compare_json()
