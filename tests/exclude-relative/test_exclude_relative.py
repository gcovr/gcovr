import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_exclude_relative(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test for excluding source files using relative filepaths."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp", "file1.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-e",
        "File1.cpp" if gcovr_test_exec.is_windows() else "file1.cpp",
        "--json-pretty",
        "--json=coverage.json",
    )

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt", "coverage.txt")
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--lcov", "coverage.lcov"
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube", "sonarqube.xml"
    )
    gcovr_test_exec.compare_sonarqube()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()


def test_exclude_relative_from_unfiltered_tracefile(
    gcovr_test_exec: "GcovrTestExec",
) -> None:
    """A simple test for excluding source files using relative filepaths from existing unfiltered JSON report."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
        gcovr_test_exec.cxx_compile("file1.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--json-pretty", "--json=coverage.json")

    gcovr_test_exec.gcovr(
        "-e",
        "file1.cpp",
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "-e", "file1.cpp", "--json-add-tracefile=coverage.json", "--txt", "coverage.txt"
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "-e",
        "file1.cpp",
        "--json-add-tracefile=coverage.json",
        "--lcov",
        "coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "-e",
        "file1.cpp",
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "-e",
        "file1.cpp",
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()

    gcovr_test_exec.gcovr(
        "-e",
        "file1.cpp",
        "--json-add-tracefile=coverage.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()
