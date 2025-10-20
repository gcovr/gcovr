import platform
import typing

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Exclusion of throw branches is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test exclude-throw-branches option, using the established output order."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

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
