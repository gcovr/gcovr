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

from tests.conftest import USE_PROFDATA_POSSIBLE, GcovrTestExec


@pytest.mark.json
@pytest.mark.txt
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.html
def test_template_function(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test template function coverage and merge-lines option."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--decision",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.gcovr(
        "--merge-lines",
        "--decision",
        "--json-pretty",
        "--json=coverage.merged.json",
    )
    gcovr_test_exec.compare_json()
    gcovr_test_exec.run("diff", "-U", "1", "coverage.json", "coverage.merged.json")

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--decision",
        "--html-self-contained",
        "--html-single-page",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--decision",
        "--html-self-contained",
        "--html-single-page",
        "--html-details=coverage.merged.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt=coverage.txt")
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--txt=coverage.merged.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura",
        "cobertura.xml",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--cobertura-pretty",
        "--cobertura",
        "cobertura.merged.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls",
        "coveralls.json",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--coveralls-pretty",
        "--coveralls",
        "coveralls.merged.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--jacoco",
        "jacoco.merged.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--lcov", "coverage.lcov"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--lcov",
        "coverage.merged.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube", "sonarqube.xml"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--sonarqube",
        "sonarqube.merged.xml",
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.json
@pytest.mark.skipif(
    not USE_PROFDATA_POSSIBLE,
    reason="LLVM profdata is not compatible with GCC coverage data.",  # noqa: F821
)
def test_template_function_llvm_profdata(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec", check
) -> None:
    """Test template function coverage and merge-lines option."""
    gcovr_test_exec.use_llvm_profdata = True

    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--decision",
        "--llvm-cov-binary=./testcase",
        "--json-pretty",
        "--json=coverage.json",
    )
    process = gcovr_test_exec.gcovr(
        "--verbose",
        "--merge-lines",
        "--decision",
        "--llvm-cov-binary=./testcase",
        "--json-pretty",
        "--json=coverage.merged.json",
    )
    gcovr_test_exec.compare_json()
    if gcovr_test_exec.cc_version() >= 12:
        check.is_not_in(
            "No branches found in LLVM JSON, this needs at least clang 12.",
            process.stderr,
        )
    else:
        check.is_in(
            "No branches found in LLVM JSON, this needs at least clang 12.",
            process.stderr,
        )
