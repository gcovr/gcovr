import typing


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test with same function const overload."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--json-pretty", "--json=coverage.json")
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json",
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
        "--clover-pretty",
        "--clover=clover.xml",
    )
    gcovr_test_exec.compare_clover()

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
