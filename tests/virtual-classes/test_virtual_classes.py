import pytest

from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
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
    gcovr_test_exec.gcovr("-d", "--json-pretty", "--json=coverage.json.xz")
    gcovr_test_exec.run("sh", "-c", "unxz -c coverage.json.xz > coverage.json")
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json.xz",
    )
    gcovr_test_exec.run(
        "sh", "-c", "unxz -c coverage_summary.json.xz > coverage_summary.json"
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--html-details=coverage.html"
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt=coverage.txt.xz")
    gcovr_test_exec.run("sh", "-c", "unxz -c coverage.txt.xz > coverage.txt")
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--clover-pretty",
        "--clover=clover.xml.xz",
    )
    gcovr_test_exec.run("sh", "-c", "unxz -c clover.xml.xz > clover.xml")
    gcovr_test_exec.compare_clover()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml.xz",
    )
    gcovr_test_exec.run("sh", "-c", "unxz -c cobertura.xml.xz > cobertura.xml")
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json.xz",
    )
    gcovr_test_exec.run("sh", "-c", "unxz -c coveralls.json.xz > coveralls.json")
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco-pretty",
        "--jacoco=jacoco.xml.xz",
    )
    gcovr_test_exec.run("sh", "-c", "unxz -c jacoco.xml.xz > jacoco.xml")
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov.xz",
    )
    gcovr_test_exec.run("sh", "-c", "unxz -c coverage.lcov.xz > coverage.lcov")
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube=sonarqube.xml.xz"
    )
    gcovr_test_exec.run("sh", "-c", "unxz -c sonarqube.xml.xz > sonarqube.xml")
    gcovr_test_exec.compare_sonarqube()
