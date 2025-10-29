import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_template_function(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test template function coverage and merge-lines option."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--decision",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.gcovr(
        "--merge-lines",
        "--decision",
        "--json-pretty",
        "--json=coverage.merged.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--decision",
        "--html-self-contained",
        "--html-single-page",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--decision",
        "--html-self-contained",
        "--html-single-page",
        "--html-details=coverage.merged.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt=coverage.txt")
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--txt=coverage.merged.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura",
        "cobertura.xml",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--cobertura-pretty",
        "--cobertura",
        "cobertura.merged.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls",
        "coveralls.json",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--coveralls-pretty",
        "--coveralls",
        "coveralls.merged.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--jacoco",
        "jacoco.merged.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--lcov", "coverage.lcov"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--lcov",
        "coverage.merged.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube", "sonarqube.xml"
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--merge-lines",
        "--sonarqube",
        "sonarqube.merged.xml",
    )
    gcovr_test_exec.compare_sonarqube()
