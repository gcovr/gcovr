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

import logging
import typing

import pytest

from tests.conftest import CONDITION_COVERAGE_POSSIBLE

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture


@pytest.mark.json
@pytest.mark.markdown
@pytest.mark.txt
@pytest.mark.clover
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.sonarqube
@pytest.mark.html
def test_standard(gcovr_exec: "GcovrExecFixture") -> None:
    """Test excluding of functions."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json",
    )
    gcovr_exec.compare_json()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--markdown=coverage.md",
    )
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--markdown-summary=coverage_summary.md",
    )
    gcovr_exec.compare_markdown()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--clover-pretty",
        "--clover=clover.xml",
    )
    gcovr_exec.compare_clover()

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
        "--sonarqube=sonarqube.xml",
    )
    gcovr_exec.compare_sonarqube()


@pytest.mark.json
@pytest.mark.txt
@pytest.mark.clover
@pytest.mark.cobertura
@pytest.mark.lcov
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.sonarqube
@pytest.mark.html
def test_stdout(gcovr_exec: "GcovrExecFixture") -> None:
    """Test excluding of functions."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--json-pretty",
        "--json",
    )
    (gcovr_exec.output_dir / "coverage.json").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--json-summary-pretty",
    )
    (gcovr_exec.output_dir / "coverage_summary.json").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_json()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html",
    )
    (gcovr_exec.output_dir / "coverage.html").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt",
    )
    (gcovr_exec.output_dir / "coverage.txt").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--clover-pretty",
        "--clover",
    )
    (gcovr_exec.output_dir / "clover.xml").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_clover()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura",
    )
    (gcovr_exec.output_dir / "cobertura.xml").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov",
    )
    (gcovr_exec.output_dir / "coverage.lcov").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_lcov()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls",
        use_main=False,
    )
    (gcovr_exec.output_dir / "coveralls.json").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_coveralls()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco",
    )
    (gcovr_exec.output_dir / "jacoco.xml").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_jacoco()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube",
    )
    (gcovr_exec.output_dir / "sonarqube.xml").write_text(
        gcovr_exec.out,
        encoding="utf-8",
    )
    gcovr_exec.compare_sonarqube()


@pytest.mark.json
@pytest.mark.csv
@pytest.mark.markdown
@pytest.mark.html
@pytest.mark.txt
@pytest.mark.clover
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
def test_directory_output(gcovr_exec: "GcovrExecFixture") -> None:
    """Test all files at once with output directory."""
    (gcovr_exec.output_dir / "output").mkdir()
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--csv",
        "--html",
        "--json",
        "--markdown",
        "--txt",
        "--clover",
        "--cobertura",
        "--coveralls",
        "--jacoco",
        "--lcov",
        "--sonarqube",
        "-o",
        ".\\output/",
        use_main=False,
    )

    for file in (gcovr_exec.output_dir / "output").glob("*.*"):
        file.rename(gcovr_exec.output_dir / file.name)
    gcovr_exec.compare_json()
    gcovr_exec.compare_csv()
    gcovr_exec.compare_markdown()
    gcovr_exec.compare_html()
    gcovr_exec.compare_txt()
    gcovr_exec.compare_clover()
    gcovr_exec.compare_cobertura()
    gcovr_exec.compare_coveralls()
    gcovr_exec.compare_jacoco()
    gcovr_exec.compare_lcov()
    gcovr_exec.compare_sonarqube()


def test_fail_under(gcovr_exec: "GcovrExecFixture") -> None:
    """Test failure thresholds."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")

    gcovr_exec.gcovr(
        "--fail-under-line=80.1",
        "--print-summary",
        exitcode_ok=2,
    )
    gcovr_exec.check_log(
        (logging.ERROR, "Failed minimum line coverage "),
        compare="startswith",
    )

    gcovr_exec.gcovr(
        "--fail-under-branch=50.1",
        "--print-summary",
        exitcode_ok=4,
    )
    gcovr_exec.check_log(
        (logging.ERROR, "Failed minimum branch coverage "),
        compare="startswith",
    )

    gcovr_exec.gcovr(
        "--decision",
        "--fail-under-condition-or-decision=50.1",
        "--print-summary",
        exitcode_ok=8,
    )
    gcovr_exec.check_log(
        *(
            # The condition coverage is only reported if the compiler supports it.
            [(logging.ERROR, "Failed minimum condition coverage ")]
            if CONDITION_COVERAGE_POSSIBLE
            else []
        ),
        (logging.ERROR, "Failed minimum decision coverage "),
        compare="startswith",
    )

    gcovr_exec.gcovr(
        "--fail-under-function=100",
        "--print-summary",
        exitcode_ok=16,
    )
    gcovr_exec.check_log(
        (logging.ERROR, "Failed minimum function coverage "),
        compare="startswith",
    )

    gcovr_exec.gcovr(
        "--fail-under-line=80.1",
        "--fail-under-branch=50.1",
        "--decision",
        "--fail-under-condition-or-decision=50.1",
        "--fail-under-function=66.8",
        "--print-summary",
        exitcode_ok=30,
    )
    gcovr_exec.check_log(
        *(
            (logging.ERROR, "Failed minimum line coverage "),
            (logging.ERROR, "Failed minimum branch coverage "),
            *(
                [(logging.ERROR, "Failed minimum condition coverage ")]
                if CONDITION_COVERAGE_POSSIBLE
                else []
            ),
            (logging.ERROR, "Failed minimum decision coverage "),
            (logging.ERROR, "Failed minimum function coverage "),
        ),
        compare="startswith",
    )

    gcovr_exec.gcovr(
        "--fail-under-line",
        "61.5" if gcovr_exec.is_llvm() else "63.6",
        "--fail-under-branch=50.0",
        "--decision",
        "--fail-under-condition-or-decision=50.0",
        "--fail-under-function=66.7",
        "--print-summary",
        use_main=False,
    )
    assert "(ERROR) Failed minimum line coverage" not in gcovr_exec.err
    assert "(ERROR) Failed minimum branch coverage" not in gcovr_exec.err
    assert "(ERROR) Failed minimum condition coverage" not in gcovr_exec.err
    assert "(ERROR) Failed minimum decision coverage" not in gcovr_exec.err
    assert "(ERROR) Failed minimum function coverage" not in gcovr_exec.err
