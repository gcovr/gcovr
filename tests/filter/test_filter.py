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

from pathlib import Path

import pytest

from tests.conftest import CXX, IS_LINUX, GcovrExecFixture


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_absolute(gcovr_exec: "GcovrExecFixture") -> None:
    """A simple test for filtering source files using absolute filepaths from existing unfiltered JSON report."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
        gcovr_exec.cxx_compile("file1.cpp"),
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        f"--filter={(gcovr_exec.output_dir / 'main.cpp').as_posix()}",
        "--json-pretty",
        "--json=coverage.json",
    )

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_exec.compare_lcov()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_exec.compare_html()

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


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_absolute_from_unfiltered_tracefile(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    """A simple test for filtering source files using absolute filepaths from existing unfiltered JSON report."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
        gcovr_exec.cxx_compile("file1.cpp"),
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr("--json-pretty", "--json", "coverage_unfiltered.json")

    filter_option = f"--filter={(gcovr_exec.output_dir / 'main.cpp').as_posix()}"

    gcovr_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--lcov=coverage.lcov",
    )
    gcovr_exec.compare_lcov()

    gcovr_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_exec.compare_jacoco()

    gcovr_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_exec.compare_sonarqube()


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_relative(gcovr_exec: "GcovrExecFixture") -> None:
    """A simple test for filtering source files using relative filepaths."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
        gcovr_exec.cxx_compile("file1.cpp"),
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--filter=main.cpp",
        "--json-pretty",
        "--json=coverage.json",
    )

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
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


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_relative_from_unfiltered_tracefile(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    """A simple test for filtering source files using relative filepaths from existing unfiltered JSON report."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
        gcovr_exec.cxx_compile("file1.cpp"),
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr("--json-pretty", "--json", "coverage_unfiltered.json")

    gcovr_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_exec.compare_jacoco()

    gcovr_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--lcov=coverage.lcov",
    )
    gcovr_exec.compare_lcov()

    gcovr_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_exec.compare_sonarqube()


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_relative_lib(gcovr_exec: "GcovrExecFixture") -> None:
    """A simple test for filtering source files using relative filepaths."""
    for entry in (gcovr_exec.output_dir / "relative_lib").glob("*"):
        entry.rename(gcovr_exec.output_dir / entry.name)
    (gcovr_exec.output_dir / "project" / "relevant-library").symlink_to(
        Path("..", "external-library"),
        target_is_directory=True,
    )
    gcovr_exec.run("sh", "-c", "ls -alR project project/relevant-library")
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile(
            "src/main.cpp",
            target="main.o",
            cwd=Path("project"),
        ),
        gcovr_exec.cxx_compile(
            "ignore-this/no.cpp",
            target="no.o",
            cwd=Path("project"),
        ),
        gcovr_exec.cxx_compile(
            "relevant-library/src/yes.cpp",
            target="yes.o",
            cwd=Path("project"),
        ),
        cwd=Path("project"),
    )

    gcovr_exec.run("./testcase", cwd=Path("project"))
    prefix = r"\.\." if gcovr_exec.is_windows() else ".*"
    gcovr_exec.gcovr(
        f"--filter={prefix}/external-library/src",
        "--json-pretty",
        "--json=../coverage.json",
        cwd=Path("project"),
    )

    gcovr_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--html-details",
        "--html=../coverage.html",
        cwd=Path("project"),
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--txt=../coverage.txt",
        cwd=Path("project"),
    )
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--cobertura-pretty",
        "--cobertura=../cobertura.xml",
        cwd=Path("project"),
    )
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--coveralls-pretty",
        "--coveralls=../coveralls.json",
        use_main=False,
        cwd=Path("project"),
    )
    gcovr_exec.compare_coveralls()

    gcovr_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--jacoco=../jacoco.xml",
        cwd=Path("project"),
    )
    gcovr_exec.compare_jacoco()

    gcovr_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--lcov=../coverage.lcov",
        cwd=Path("project"),
    )
    gcovr_exec.compare_lcov()

    gcovr_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--sonarqube=../sonarqube.xml",
        cwd=Path("project"),
    )
    gcovr_exec.compare_sonarqube()


@pytest.mark.cobertura
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_relative_lib_from_unfiltered_tracefile(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    """A simple test for filtering source files using relative filepaths."""
    for entry in (gcovr_exec.output_dir / "relative_lib").glob("*"):
        entry.rename(gcovr_exec.output_dir / entry.name)
    (gcovr_exec.output_dir / "project" / "relevant-library").symlink_to(
        Path("..", "external-library"),
        target_is_directory=True,
    )
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile(
            "src/main.cpp",
            target="main.o",
            cwd=Path("project"),
        ),
        gcovr_exec.cxx_compile(
            "ignore-this/no.cpp",
            target="no.o",
            cwd=Path("project"),
        ),
        gcovr_exec.cxx_compile(
            "relevant-library/src/yes.cpp",
            target="yes.o",
            cwd=Path("project"),
        ),
        cwd=Path("project"),
    )

    gcovr_exec.run("./testcase", cwd=Path("project"))
    gcovr_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--json-pretty",
        "--json=../coverage.json",
        cwd=Path("project"),
    )

    gcovr_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--txt=../coverage.txt",
        cwd=Path("project"),
    )
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--jacoco=../jacoco.xml",
        cwd=Path("project"),
    )
    gcovr_exec.compare_jacoco()

    gcovr_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--lcov=../coverage.lcov",
        cwd=Path("project"),
    )
    gcovr_exec.compare_lcov()

    gcovr_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--cobertura-pretty",
        "--cobertura=../cobertura.xml",
        cwd=Path("project"),
    )
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--sonarqube=../sonarqube.xml",
        cwd=Path("project"),
    )
    gcovr_exec.compare_sonarqube()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="File inclusion is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.json
def test_include(gcovr_exec: "GcovrExecFixture") -> None:
    """Test include filtering and multiple HTML themes."""
    # Compile file1.cpp without coverage flags, then main.cpp with coverage
    gcovr_exec.run(CXX, "-fPIC", "-c", "file1.cpp", "-o", "file1.o")
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
        "file1.o",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--verbose",
        "--include=file1.cpp",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_exec.compare_json()
