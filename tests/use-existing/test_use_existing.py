import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """A test that verifies coverage when using existing *.gcov coverage files with verbose output.
    All files identical to tests/simple1 except for this README file and Makefile"""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.run(
        *gcovr_test_exec.gcov(),
        *list(gcovr_test_exec.output_dir.glob("*.gcda")),
        "--branch-counts",
        "--branch-probabilities",
        "--preserve-paths",
    )
    gcovr_test_exec.gcovr(
        "--gcov-use-existing-files",
        "--gcov-delete",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt=coverage.txt")
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

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--jacoco=jacoco.xml")
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--lcov=coverage.lcov")
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube=sonarqube.xml"
    )
    gcovr_test_exec.compare_sonarqube()
