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

from tests.conftest import IS_LINUX, GcovrTestExec


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Split of signature is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.html
@pytest.mark.clover
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test split-signature coverage."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--json-pretty", "--json=coverage.json"
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--delete-input-files", "--html-details=coverage.html")
    gcovr_test_exec.compare_html()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--delete-input-files", "--txt", "coverage.txt")
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--clover-pretty", "--clover", "clover.xml"
    )
    gcovr_test_exec.compare_clover()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--cobertura-pretty", "--cobertura", "cobertura.xml"
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--coveralls-pretty", "--coveralls", "coveralls.json"
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--jacoco-pretty", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--delete-input-files", "--lcov", "coverage.lcov")
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--delete-input-files", "--sonarqube", "sonarqube.xml")
    gcovr_test_exec.compare_sonarqube()
