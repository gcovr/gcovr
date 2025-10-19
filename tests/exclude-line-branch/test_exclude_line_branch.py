import platform
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Exclusion markers are independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
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
