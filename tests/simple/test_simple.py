import logging
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_standard(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test excluding of functions."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
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
        "--markdown=coverage.md",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--markdown-summary=coverage_summary.md",
    )
    gcovr_test_exec.compare_markdown()

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
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


def test_stdout(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test excluding of functions."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    (gcovr_test_exec.output_dir / "coverage.json").write_text(
        gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json",
        ).stdout,
        encoding="utf-8",
    )
    (gcovr_test_exec.output_dir / "coverage_summary.json").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--json-summary-pretty",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_json()

    (gcovr_test_exec.output_dir / "coverage.html").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--html",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_html()

    (gcovr_test_exec.output_dir / "coverage.txt").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--txt",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_txt()

    (gcovr_test_exec.output_dir / "clover.xml").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--clover-pretty",
            "--clover",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_clover()

    (gcovr_test_exec.output_dir / "cobertura.xml").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--cobertura-pretty",
            "--cobertura",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_cobertura()

    (gcovr_test_exec.output_dir / "coverage.lcov").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--lcov",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_lcov()

    (gcovr_test_exec.output_dir / "coveralls.json").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--coveralls-pretty",
            "--coveralls",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_coveralls()

    (gcovr_test_exec.output_dir / "jacoco.xml").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--jacoco",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_jacoco()

    (gcovr_test_exec.output_dir / "sonarqube.xml").write_text(
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--sonarqube",
        ).stdout,
        encoding="utf-8",
    )
    gcovr_test_exec.compare_sonarqube()


def test_directory_output(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test all files at once with output directory."""
    (gcovr_test_exec.output_dir / "output").mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--csv",
        "--html",
        "--json",
        "--markdown",
        "--txt",
        "--clover",
        "--cobertura",
        "--coveralls",
        "--jacoco",
        "--lcov",
        "--sonarqube",
        "-o",
        ".\\output/",
    )

    for file in (gcovr_test_exec.output_dir / "output").glob("*.*"):
        file.rename(gcovr_test_exec.output_dir / file.name)
    gcovr_test_exec.compare_csv()
    gcovr_test_exec.compare_json()
    gcovr_test_exec.compare_markdown()
    gcovr_test_exec.compare_html()
    gcovr_test_exec.compare_txt()
    gcovr_test_exec.compare_clover()
    gcovr_test_exec.compare_cobertura()
    gcovr_test_exec.compare_coveralls()
    gcovr_test_exec.compare_jacoco()
    gcovr_test_exec.compare_lcov()
    gcovr_test_exec.compare_sonarqube()


def test_fail_under(
    gcovr_test_exec: "GcovrTestExec", caplog: pytest.LogCaptureFixture
) -> None:
    """Test failure thresholds."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")

    process = gcovr_test_exec.gcovr(
        "--fail-under-line=80.1",
        "--print-summary",
        use_main=True,
    )
    assert process.returncode == 2
    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.ERROR
    assert messages[0][2].startswith("Failed minimum line coverage ")
    caplog.clear()

    process = gcovr_test_exec.gcovr(
        "--fail-under-branch=50.1",
        "--print-summary",
        use_main=True,
    )
    assert process.returncode == 4
    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.ERROR
    assert messages[0][2].startswith("Failed minimum branch coverage ")
    caplog.clear()

    process = gcovr_test_exec.gcovr(
        "--decision",
        "--fail-under-decision=50.1",
        "--print-summary",
        use_main=True,
    )
    assert process.returncode == 8
    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.ERROR
    assert messages[0][2].startswith("Failed minimum decision coverage ")
    caplog.clear()

    process = gcovr_test_exec.gcovr(
        "--fail-under-function=100",
        "--print-summary",
        use_main=True,
    )
    assert process.returncode == 16
    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.ERROR
    assert messages[0][2].startswith("Failed minimum function coverage ")
    caplog.clear()

    process = gcovr_test_exec.gcovr(
        "--fail-under-line=80.1",
        "--fail-under-branch=50.1",
        "--decision",
        "--fail-under-decision=50.1",
        "--fail-under-function=66.8",
        "--print-summary",
        use_main=True,
    )
    assert process.returncode == 30
    messages = caplog.record_tuples
    assert len(messages) == 4
    assert messages[0][1] == logging.ERROR
    assert messages[0][2].startswith("Failed minimum line coverage ")
    assert messages[1][1] == logging.ERROR
    assert messages[1][2].startswith("Failed minimum branch coverage ")
    assert messages[2][1] == logging.ERROR
    assert messages[2][2].startswith("Failed minimum decision coverage ")
    assert messages[3][1] == logging.ERROR
    assert messages[3][2].startswith("Failed minimum function coverage ")
    caplog.clear()

    process = gcovr_test_exec.gcovr(
        "--fail-under-line",
        "61.5" if gcovr_test_exec.is_llvm() else "63.6",
        "--fail-under-branch=50.0",
        "--decision",
        "--fail-under-decision=50.0",
        "--fail-under-function=66.7",
        "--print-summary",
        use_main=True,
    )
    assert process.returncode == 0
    assert "(ERROR) Failed minimum line coverage" not in process.stderr
    assert "(ERROR) Failed minimum branch coverage" not in process.stderr
    assert "(ERROR) Failed minimum decision coverage" not in process.stderr
    assert "(ERROR) Failed minimum function coverage" not in process.stderr
