import pytest

from tests.conftest import IS_LINUX, GcovrTestExec


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Split of signature is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test split-signature coverage."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--json-pretty", "--json=coverage.json")
    gcovr_test_exec.compare_json()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--html-details=coverage.html")
    gcovr_test_exec.compare_html()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--txt", "coverage.txt")
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--clover-pretty", "--clover", "clover.xml")
    gcovr_test_exec.compare_clover()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--cobertura-pretty", "--cobertura", "cobertura.xml")
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--coveralls-pretty", "--coveralls", "coveralls.json")
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--jacoco-pretty", "--jacoco", "jacoco.xml")
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--lcov", "coverage.lcov")
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--sonarqube", "sonarqube.xml")
    gcovr_test_exec.compare_sonarqube()
