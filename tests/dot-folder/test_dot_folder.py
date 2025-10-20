import platform
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Dor-folders have no special meaning on Windows and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    (gcovr_test_exec.output_dir / "subdir").rename(
        gcovr_test_exec.output_dir / ".subdir"
    )
    gcovr_test_exec.cxx_link(
        ".subdir/testcase",
        *[
            gcovr_test_exec.cxx_compile(source, target=source + ".o", options=["-DFOO"])
            for source in [
                ".subdir/A/file1.cpp",
                ".subdir/A/File2.cpp",
                ".subdir/A/file3.cpp",
                ".subdir/A/File4.cpp",
                ".subdir/A/C/file5.cpp",
                ".subdir/A/C/D/File6.cpp",
                ".subdir/B/main.cpp",
            ]
        ],
    )

    gcovr_test_exec.run(".subdir/testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
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
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()
