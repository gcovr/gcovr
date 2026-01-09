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

import re
import pytest

from tests.conftest import IS_DARWIN, IS_GCC, IS_LINUX, GcovrTestExec


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Exclusion markers are independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_exclude_line(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test excluding of functions."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "--warn-excluded-lines-with-hits",
        "--json-pretty",
        "--json=coverage.json",
    )
    check.is_in("main.cpp:8: Line with 1 hit(s) excluded.", process.stderr)
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Exclusion markers are independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_exclude_line_custom(gcovr_test_exec: "GcovrTestExec") -> None:
    """This test case verifies that custom tagged lines (LINE/START/STOP) are excluded per run options.
    It uses exclude_pattern_prefix to pass a custom prefix."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--exclude-pattern-prefix=CUSTOM",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--exclude-pattern-prefix=CUSTOM",
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--exclude-pattern-prefix=CUSTOM",
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--exclude-pattern-prefix=CUSTOM",
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--exclude-pattern-prefix=CUSTOM",
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--exclude-pattern-prefix=CUSTOM",
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--exclude-pattern-prefix=CUSTOM",
        "--json-add-tracefile=coverage.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--exclude-pattern-prefix=CUSTOM",
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Exclusion markers are independent of OS and we do not want to have separate data for Windows and Darwin.",
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
def test_exclude_line_branch(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test for --exclude-unreachable-branches option.

    The test attempts to test both GCOV/LCOV exclusion markers
    and auto-detection of compiler-generated code.
    """
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
        "foo.cpp",
        "bar.cpp",
    )

    cwd = gcovr_test_exec.output_dir.parent

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--exclude-unreachable-branches",
        "--keep",
        "--json-pretty",
        "--json",
        gcovr_test_exec.output_dir / "coverage.json",
        gcovr_test_exec.output_dir,
        cwd=cwd,
    )
    gcovr_test_exec.gcovr(
        "--exclude-unreachable-branches",
        "--json-summary-pretty",
        "--json-summary",
        gcovr_test_exec.output_dir / "coverage_summary.json",
        gcovr_test_exec.output_dir,
        cwd=cwd,
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile",
        gcovr_test_exec.output_dir / "coverage.json",
        "--html-details",
        gcovr_test_exec.output_dir / "coverage.html",
        cwd=cwd,
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile",
        gcovr_test_exec.output_dir / "coverage.json",
        "--txt",
        gcovr_test_exec.output_dir / "coverage.txt",
        cwd=cwd,
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile",
        gcovr_test_exec.output_dir / "coverage.json",
        "--clover-pretty",
        "--clover",
        gcovr_test_exec.output_dir / "clover.xml",
        cwd=cwd,
    )
    gcovr_test_exec.compare_clover()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile",
        gcovr_test_exec.output_dir / "coverage.json",
        "--cobertura-pretty",
        "--cobertura",
        gcovr_test_exec.output_dir / "cobertura.xml",
        cwd=cwd,
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile",
        gcovr_test_exec.output_dir / "coverage.json",
        "--coveralls-pretty",
        "--coveralls",
        gcovr_test_exec.output_dir / "coveralls.json",
        cwd=cwd,
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile",
        gcovr_test_exec.output_dir / "coverage.json",
        "--jacoco",
        gcovr_test_exec.output_dir / "jacoco.xml",
        cwd=cwd,
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile",
        gcovr_test_exec.output_dir / "coverage.json",
        "--lcov",
        gcovr_test_exec.output_dir / "coverage.lcov",
        cwd=cwd,
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile",
        gcovr_test_exec.output_dir / "coverage.json",
        "--sonarqube",
        gcovr_test_exec.output_dir / "sonarqube.xml",
        cwd=cwd,
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_exclude_lines_by_pattern(gcovr_test_exec: "GcovrTestExec") -> None:
    """This test case verifies that custom tagged lines (LINE/START/STOP) are excluded per run options.
    It uses exclude_pattern_prefix to pass a custom prefix."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--config=config/gcovr.config",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--exclude-lines-by-pattern= *panic\\([^)]*\\);",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    (gcovr_test_exec.output_dir / "config" / "pyproject.toml").rename(
        gcovr_test_exec.output_dir / "pyproject.toml"
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Exclusion markers are independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_exclude_branch(gcovr_test_exec: "GcovrTestExec") -> None:
    """This test case verifies that tagged lines (BR_LINE/BR_START/BR_STOP) are excluded per run options."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--no-markers",
        "--json-pretty",
        "--json=coverage.no-markers.json",
    )
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Exclusion markers are independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_exclude_branch_source(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test exclusion of source branches, following the output order from exclude-line-custom."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--no-markers",
        "--json-pretty",
        "--json=coverage.no-markers.json",
    )
    process = gcovr_test_exec.gcovr(
        "--verbose",
        "--json-pretty",
        "--json=coverage.json",
        "--trace-include=.*main.cpp",
    )
    gcovr_test_exec.compare_json()

    file = gcovr_test_exec.output_dir / "main.cpp"
    check.is_in(
        f"Found marker for source branch exclusion at {file}:4:7 without coverage information",
        process.stderr,
    )
    # If block_ids entry is found the compiler supports the function excludes else we need to see a warning.
    if '"block_ids"' in (gcovr_test_exec.output_dir / "coverage.json").read_text(
        encoding="utf-8"
    ):
        check.is_in(
            f"Source branch exclusion at {file}:11:20 is excluding branch 2->5 of line 5",
            process.stderr,
        )
        check.is_in(
            f"Source branch exclusion at {file}:19:39 found but no block ids defined at this line",
            process.stderr,
        )
        check.is_in(
            f"Source branch exclusion at {file}:24:45 is excluding branch 8->11 of line 20",
            process.stderr,
        )
    else:
        check.is_in(
            f"Source branch exclusion at {file}:11:20 needs at least gcc-14 with supported JSON format.",
            process.stderr,
        )
        check.is_in(
            f"Source branch exclusion at {file}:19:39 needs at least gcc-14 with supported JSON format.",
            process.stderr,
        )
        check.is_in(
            f"Source branch exclusion at {file}:24:45 needs at least gcc-14 with supported JSON format.",
            process.stderr,
        )

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt", "coverage.txt")
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--lcov", "coverage.lcov"
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube", "sonarqube.xml"
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_exclude_branch_without_hit(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test exclusion of source branches, following the output order from exclude-line-custom."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--no-markers",
        "--json-pretty",
        "--json=coverage.no-markers.json",
    )
    process = gcovr_test_exec.gcovr(
        "--verbose",
        "--json-pretty",
        "--json=coverage.json",
        "--trace-include=.*main.cpp",
    )
    gcovr_test_exec.compare_json()

    file = gcovr_test_exec.output_dir / "main.cpp"
    check.is_in(
        f"Found marker for exclusion of branches without hits at {file}:4:7 without coverage information",
        process.stderr,
    )
    if '"block_ids"' in (gcovr_test_exec.output_dir / "coverage.json").read_text(
        encoding="utf-8"
    ):
        check.is_in(
            f"Exclusion of branches without hits at {file}:5:24 is excluding 2 branch(es)",
            process.stderr,
        )
    else:
        check.is_in(
            f"Exclusion of branches without hits (2/4) at {file}:5:24 is wrong. There are 3 out of 5 branches uncovered",
            process.stderr,
        )
    x_out_of_y = "2 out of 4" if gcovr_test_exec.is_llvm() else "3 out of 6"
    check.is_in(
        f"Exclusion of branches without hits (2/6) at {file}:20:31 is wrong. There are {x_out_of_y} branches uncovered",
        process.stderr,
    )

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt", "coverage.txt")
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--lcov", "coverage.lcov"
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube", "sonarqube.xml"
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Exclusion of throw branches is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_exclude_throw_branches(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test exclude-throw-branches option."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--json-pretty", "--json=coverage-throw.json")
    process = gcovr_test_exec.gcovr(
        "--exclude-throw-branches",
        "--trace-include=.*",
        "--json-pretty",
        "--json=coverage-exclude-throw.json",
    )
    lines = [5, 28, 33, 36, 41] if IS_GCC else []
    for line in lines:
        check.is_true(
            re.search(
                rf"main.cpp:{line}: Removing \d+ unreachable branch\(es\) detected as exception-only code",
                process.stderr,
            ),
            f"Expected exclusion message for throw branch at line {line} not found in stderr.",
        )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-throw.json",
        "--html-details",
        "--html=coverage-throw.html",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-exclude-throw.json",
        "--html-details",
        "--html=coverage-exclude-throw.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-throw.json", "--txt=coverage-throw.txt"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-exclude-throw.json",
        "--txt=coverage-exclude-throw.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-throw.json", "--cobertura=cobertura-throw.xml"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-exclude-throw.json",
        "--cobertura=cobertura-exclude-throw.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-throw.json",
        "--coveralls-pretty",
        "--coveralls=coveralls-throw.json",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-exclude-throw.json",
        "--coveralls-pretty",
        "--coveralls=coveralls-exclude-throw.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-throw.json", "--lcov=coverage-throw.lcov"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-exclude-throw.json",
        "--lcov=coverage-exclude-throw.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-throw.json", "--jacoco=jacoco-throw.xml"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-exclude-throw.json",
        "--jacoco=jacoco-exclude-throw.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-throw.json", "--sonarqube=sonarqube-throw.xml"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage-exclude-throw.json",
        "--sonarqube=sonarqube-exclude-throw.xml",
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_exclude_directories_relative(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test for excluding gcov files using relative directory paths."""
    (gcovr_test_exec.output_dir / "build" / "a").mkdir(parents=True)
    (gcovr_test_exec.output_dir / "build" / "b").mkdir(parents=True)
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("a/file1.cpp", target="build/a/file.o"),
        gcovr_test_exec.cxx_compile("b/main.cpp", target="build/b/main.o"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--gcov-exclude-directory",
        "build/a",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.json
def test_exclude_file_relative(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test for excluding source files using relative filepaths."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp", "file1.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.no-markers.json",
    )
    gcovr_test_exec.gcovr(
        f"--exclude={'File1.cpp' if gcovr_test_exec.is_windows() else 'file1.cpp'}",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Exclusion markers are independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.json
def test_exclude_function(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test excluding of functions."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "--exclude-function",
        "sort_excluded_both()::{lambda(int, int)#2}::operator()(int, int) const",
        "--exclude-function",
        "/bar.+/",
        "--json-pretty",
        "--json=coverage.json",
    )
    coverage_json_content = (gcovr_test_exec.output_dir / "coverage.json").read_text(
        encoding="utf-8"
    )
    if '"pos"' in coverage_json_content:
        for pos in ["9:8", "50:19"]:
            with check:
                assert (
                    f"Function exclude marker found on line {pos} but no function definition found"
                    in process.stderr
                )

        def assert_stderr(string: str) -> None:
            assert string not in process.stderr
    else:

        def assert_stderr(string: str) -> None:
            assert string in process.stderr

    positions = ["9:8", "50:19"]
    if gcovr_test_exec.is_cxx_lambda_expression_available():
        positions += ["44:29", "50:19", "57:29", "66:34", "73:29"]
    for pos in positions:
        with check:
            assert_stderr(
                f"Function exclude marker found on line {pos} but not supported for this compiler"
            )

    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    IS_DARWIN,
    reason="Exclude Darwin to not have separate reference.",
)
@pytest.mark.json
def test_gcov_exclude(gcovr_test_exec: "GcovrTestExec") -> None:
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
    )

    gcovr_test_exec.run("./subdir/testcase")
    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--gcov-exclude-directory=.*/A/C(?:/.*)?",
        "--gcov-filter=.*",
        "--gcov-exclude=subdir#A#[Ff]ile.\\.cpp\\.gcov",
        "--gcov-exclude=[Ff]ile.\\.cpp##.*",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
