#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.7, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.7
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


@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.html
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test(gcovr_exec: "GcovrExecFixture") -> None:
    """Test workspace coverage."""
    gcovr_exec.cxx_link("testcase", "main.cpp", cwd=Path("src code"))
    gcovr_exec.run("./testcase", cwd=Path("src code"))
    gcovr_exec.gcovr(
        "--root=src code",
        "--json-pretty",
        "--json=coverage.json",
        "--html-details=coverage.html",
        "--txt=coverage.txt",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
        "--jacoco-pretty",
        "--jacoco=jacoco.xml",
        "--lcov=coverage.lcov",
        "--sonarqube=sonarqube.xml",
        use_main=False,
    )
    gcovr_exec.compare_json()
    gcovr_exec.compare_html()
    gcovr_exec.compare_txt()
    gcovr_exec.compare_cobertura()
    gcovr_exec.compare_coveralls()
    gcovr_exec.compare_jacoco()
    gcovr_exec.compare_lcov()
    gcovr_exec.compare_sonarqube()
