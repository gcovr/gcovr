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

import pytest

from tests.conftest import IS_WINDOWS, GcovrExecFixture


@pytest.mark.skipif(
    IS_WINDOWS,
    reason="Dot-folders have no special meaning on Windows and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test(gcovr_exec: "GcovrExecFixture") -> None:
    """Test adding a tracefile output."""
    (gcovr_exec.output_dir / "subdir").rename(gcovr_exec.output_dir / ".subdir")
    gcovr_exec.cxx_link(
        ".subdir/testcase",
        *[
            gcovr_exec.cxx_compile(source, target=source + ".o", options=["-DFOO"])
            for source in [
                ".subdir/A/file1.cpp",
                ".subdir/A/File2.cpp",
                ".subdir/A/file3.cpp",
                ".subdir/A/File4.cpp",
                ".subdir/A/C/file5.cpp",
                ".subdir/A/C/D/File6.cpp",
                ".subdir/B/main.cpp",
            ]
        ],
    )

    gcovr_exec.run(".subdir/testcase")
    gcovr_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_exec.compare_json()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
        use_main=False,
    )
    gcovr_exec.compare_coveralls()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_exec.compare_jacoco()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_exec.compare_lcov()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_exec.compare_sonarqube()
