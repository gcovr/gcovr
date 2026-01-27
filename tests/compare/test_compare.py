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

PARAMETERS = [
    (
        "strictly-equal",
        1,
        [],
    ),
    (
        "approximately-equal",
        2,
        [],
    ),
    (
        "changed",
        2,
        ["1"],
    ),
]


@pytest.mark.json
@pytest.mark.txt
@pytest.mark.parametrize(
    "_test_id,runs,run_options",
    PARAMETERS,
    ids=[p[0] for p in PARAMETERS],
)
def test(
    gcovr_test_exec: "GcovrTestExec",
    _test_id: str,
    runs: int,
    run_options: list[str],
) -> None:
    """Test with same function const overload."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--json-pretty", "--json=coverage_1.json"
    )
    for _ in range(0, runs):
        gcovr_test_exec.run("./testcase", *run_options)
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--json-pretty", "--json=coverage_2.json"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage_1.json",
        "--json-add-tracefile=coverage_2.json",
        "--json-compare",
        "--json-pretty",
        "--json=coverage_compare.json",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage_compare.json",
        "--json-pretty",
        "--json=coverage_compare_roundtrip.json",
    )
    gcovr_test_exec.run(
        "diff", "-U", "1", "coverage_compare.json", "coverage_compare_roundtrip.json"
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage_compare.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()
