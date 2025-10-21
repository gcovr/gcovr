import platform
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Exclusion markers are independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_exclude_branch(gcovr_test_exec: "GcovrTestExec") -> None:
    """This test case verifies that tagged lines (BR_LINE/BR_START/BR_STOP) are excluded per run options."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main_exclude_branch.cpp",
    )

    gcovr_test_exec.run("./testcase")
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
    platform.system() != "Linux",
    reason="Exclusion markers are independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_exclude_branch_source(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test exclusion of source branches, following the output order from exclude-line-custom."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main_exclude_branch_source.cpp",
    )

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "-v",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    file = gcovr_test_exec.output_dir / "main_exclude_branch_source.cpp"
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


def test_exclude_branch_without_hit(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test exclusion of source branches, following the output order from exclude-line-custom."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main_exclude_branch_without_hit.cpp",
    )

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "-v",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    file = gcovr_test_exec.output_dir / "main_exclude_branch_without_hit.cpp"
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
    platform.system() != "Linux",
    reason="Exclusion of throw branches is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_exclude_throw_branches(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test exclude-throw-branches option."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main_exclude_throw_branches.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--gcov-keep", "--json-pretty", "--json=coverage-throw.json")
    gcovr_test_exec.gcovr(
        "--gcov-keep",
        "--exclude-throw-branches",
        "--json-pretty",
        "--json=coverage-exclude-throw.json",
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
