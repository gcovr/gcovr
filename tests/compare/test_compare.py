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
        "equal",
        1,
        [],
    ),
    (
        "changed",
        2,
        ["123456789"],
    ),
]


@pytest.mark.json
@pytest.mark.txt
@pytest.mark.html
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
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
    )

    gcovr_test_exec.run("./subdir/testcase")
    gcovr_options = ["--exclude", ".*/file1.cpp"] if run_options else []
    gcovr_test_exec.gcovr(
        "--delete-input-files",
        *gcovr_options,
        "--json-pretty",
        "--json=coverage_1.json",
    )
    for _ in range(0, runs):
        gcovr_test_exec.run("./subdir/testcase", *run_options)
    gcovr_options = ["--exclude", ".*/file3.cpp"] if run_options else []
    gcovr_test_exec.gcovr(
        "--delete-input-files",
        *gcovr_options,
        "--json-pretty",
        "--json=coverage_2.json",
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
    (gcovr_test_exec.output_dir / "coverage_compare_roundtrip.json").unlink()
    gcovr_test_exec.compare_json()

    process = gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage_compare.json",
        "--txt-summary",
        "--txt=coverage.txt",
    )
    (gcovr_test_exec.output_dir / "coverage_summary.txt").write_text(
        process.stdout, encoding="utf-8"
    )
    gcovr_test_exec.compare_txt()

    process = gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage_compare.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()
