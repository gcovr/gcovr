import pytest

from tests.conftest import GcovrTestExec


@pytest.mark.xfail(
    GcovrTestExec.is_gcc() and GcovrTestExec.cc_version() in [5, 6],
    reason="The branch and call numbers differ in locale execution and CI",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test virtual-classes coverage."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--json-pretty", "--json=coverage.json.gz")
    gcovr_test_exec.run("sh", "-c", "gunzip -c coverage.json.gz > coverage.json")
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json.gz",
    )
    gcovr_test_exec.run(
        "sh", "-c", "gunzip -c coverage_summary.json.gz > coverage_summary.json"
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--html-details=coverage.html"
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt=coverage.txt.gz")
    gcovr_test_exec.run("sh", "-c", "gunzip -c coverage.txt.gz > coverage.txt")
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--clover-pretty",
        "--clover=clover.xml.gz",
    )
    gcovr_test_exec.run("sh", "-c", "gunzip -c clover.xml.gz > clover.xml")
    gcovr_test_exec.compare_clover()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml.gz",
    )
    gcovr_test_exec.run("sh", "-c", "gunzip -c cobertura.xml.gz > cobertura.xml")
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json.gz",
    )
    gcovr_test_exec.run("sh", "-c", "gunzip -c coveralls.json.gz > coveralls.json")
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco-pretty",
        "--jacoco=jacoco.xml.gz",
    )
    gcovr_test_exec.run("sh", "-c", "gunzip -c jacoco.xml.gz > jacoco.xml")
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov.gz",
    )
    gcovr_test_exec.run("sh", "-c", "gunzip -c coverage.lcov.gz > coverage.lcov")
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube=sonarqube.xml.gz"
    )
    gcovr_test_exec.run("sh", "-c", "gunzip -c sonarqube.xml.gz > sonarqube.xml")
    gcovr_test_exec.compare_sonarqube()
