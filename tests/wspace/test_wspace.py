from pathlib import Path
import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test workspace coverage."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp", cwd=Path("src code"))
    gcovr_test_exec.run("./testcase", cwd=Path("src code"))
    gcovr_test_exec.gcovr(
        "--root=src code",
        "--json-pretty",
        "--json=coverage.json",
        "--html-details=coverage.html",
        "--txt=coverage.txt",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
        "--jacoco-pretty",
        "--jacoco=jacoco.xml",
        "--lcov=coverage.lcov",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_json()
    gcovr_test_exec.compare_html()
    gcovr_test_exec.compare_txt()
    gcovr_test_exec.compare_cobertura()
    gcovr_test_exec.compare_coveralls()
    gcovr_test_exec.compare_jacoco()
    gcovr_test_exec.compare_lcov()
    gcovr_test_exec.compare_sonarqube()
