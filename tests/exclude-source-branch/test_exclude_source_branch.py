import platform
import typing

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Exclusion markers are independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_exclude_source_branch(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test exclusion of source branches, following the output order from exclude-line-custom."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "-v",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    file = gcovr_test_exec.output_dir / "main.cpp"
    check.is_in("4:7 without coverage information", process.stderr)
    # If block_ids entry is found the compiler supports the function excludes else we need to see a warning.
    if '"block_ids"' in (gcovr_test_exec.output_dir / "coverage.json").read_text(
        encoding="utf-8"
    ):
        check.is_in(f"{file}:12:20 is excluding branch 2->5 of line 6", process.stderr)
        check.is_in(
            f"{file}:20:39 found but no block ids defined at this line", process.stderr
        )
        check.is_in(
            f"{file}:25:45 is excluding branch 8->11 of line 21", process.stderr
        )
    else:
        check.is_in(
            f"{file}:12:20 needs at least gcc-14 with supported JSON format.",
            process.stderr,
        )
        check.is_in(
            f"{file}:20:39 needs at least gcc-14 with supported JSON format.",
            process.stderr,
        )
        check.is_in(
            f"{file}:25:45 needs at least gcc-14 with supported JSON format.",
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


def test_exclude_source_branch_without_hit(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test exclusion of source branches, following the output order from exclude-line-custom."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "-v",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    file = gcovr_test_exec.output_dir / "main.cpp"
    with check:
        assert f"{file}:4:7 without coverage information" in process.stderr
    x_out_of_y = (
        "2 out of 4"
        if gcovr_test_exec.is_llvm()
        else "3 out of 6"
        if gcovr_test_exec.cc_version() < 14
        else "2 out of 5"
    )
    with check:
        assert (
            f"(2/6) at {file.resolve()}:21:31 is wrong. There are {x_out_of_y} branches uncovered"
            in process.stderr
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
