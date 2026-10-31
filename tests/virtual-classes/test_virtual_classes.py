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

import pytest

from tests.conftest import GcovrExecFixture


@pytest.mark.skipif(
    GcovrExecFixture.is_gcc() and GcovrExecFixture.cc_version() in [5, 6],
    reason="The branch and call numbers differ in locale execution and CI",
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
def test(gcovr_exec: "GcovrExecFixture") -> None:
    """Test virtual-classes coverage."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr("--delete-input-files", "--json-pretty", "--json=coverage.json.xz")
    gcovr_exec.run("sh", "-c", "unxz -c coverage.json.xz > coverage.json")
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json.xz",
    )
    gcovr_exec.run(
        "sh", "-c", "unxz -c coverage_summary.json.xz > coverage_summary.json"
    )
    gcovr_exec.compare_json()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--html-details=coverage.html"
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr("--json-add-tracefile=coverage.json", "--txt=coverage.txt.xz")
    gcovr_exec.run("sh", "-c", "unxz -c coverage.txt.xz > coverage.txt")
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--clover-pretty",
        "--clover=clover.xml.xz",
    )
    gcovr_exec.run("sh", "-c", "unxz -c clover.xml.xz > clover.xml")
    gcovr_exec.compare_clover()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml.xz",
    )
    gcovr_exec.run("sh", "-c", "unxz -c cobertura.xml.xz > cobertura.xml")
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json.xz",
        use_main=False,
    )
    gcovr_exec.run("sh", "-c", "unxz -c coveralls.json.xz > coveralls.json")
    gcovr_exec.compare_coveralls()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco-pretty",
        "--jacoco=jacoco.xml.xz",
    )
    gcovr_exec.run("sh", "-c", "unxz -c jacoco.xml.xz > jacoco.xml")
    gcovr_exec.compare_jacoco()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov.xz",
    )
    gcovr_exec.run("sh", "-c", "unxz -c coverage.lcov.xz > coverage.lcov")
    gcovr_exec.compare_lcov()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube=sonarqube.xml.xz"
    )
    gcovr_exec.run("sh", "-c", "unxz -c sonarqube.xml.xz > sonarqube.xml")
    gcovr_exec.compare_sonarqube()
