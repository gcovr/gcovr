import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """This test case verifies that custom tagged lines (LINE/START/STOP) are excluded per run options.
    It uses exclude_pattern_prefix to pass a custom prefix."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--config=config/gcovr.config",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--exclude-lines-by-pattern= *panic\\([^)]*\\);",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    (gcovr_test_exec.output_dir / "config" / "pyproject.toml").rename(
        gcovr_test_exec.output_dir / "pyproject.toml"
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()
