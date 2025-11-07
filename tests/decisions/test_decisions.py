from pathlib import Path
import pytest


from tests.conftest import IS_LINUX, USE_PROFDATA_POSSIBLE, GcovrTestExec


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Parsing of decision is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
def test_decisions(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test of decision parsing."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
        "switch_test.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--keep",
        "--verbose",
        "--decisions",
        "--json-pretty",
        "--json=coverage.json.gz",
    )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile=coverage.json.gz",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile=coverage.json.gz",
        "--decision",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile=coverage.json.gz",
        "--decision",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()

    process = gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile=coverage.json.gz",
        "--txt-metric=decision",
        "--txt-summary",
        "--txt=coverage.txt",
    )
    (gcovr_test_exec.output_dir / "coverage_summary.txt").write_text(
        process.stdout, encoding="utf-8"
    )
    gcovr_test_exec.compare_txt()


@pytest.mark.skipif(
    not USE_PROFDATA_POSSIBLE,
    reason="Parsing of decision is independent of OS and we do not want to have separate data for Windows and Darwin and LLVM profdata is not compatible with GCC coverage data.",
)
def test_decisions_llvm_profdata(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test of decision parsing."""
    gcovr_test_exec.use_llvm_profdata = True
    gcovr_test_exec.copy_source(Path("source", "decisions"))

    mcdc_supported_by_compiler = gcovr_test_exec.is_in_gcc_help("coverage-mcdc")
    additional_options = []
    if mcdc_supported_by_compiler:
        additional_options.append("-fcoverage-mcdc")

    gcovr_test_exec.cxx_link(
        "testcase",
        *additional_options,
        "main.cpp",
        "switch_test.cpp",
    )

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "--verbose",
        "--delete-input-files",
        "--decisions",
        "--llvm-cov-binary=./testcase",
        "--json-pretty",
        "--json=coverage.json.gz",
        "default.profraw",
    )
    if mcdc_supported_by_compiler:
        check.is_in(
            "Found 'mcdc_records' in exported JSON report. This is ignored by GCOVR.",
            process.stderr,
        )
    else:
        check.is_not_in(
            "Found 'mcdc_records' in exported JSON report. This is ignored by GCOVR.",
            process.stderr,
        )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile=coverage.json.gz",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile=coverage.json.gz",
        "--decision",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json",
    )
    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Parsing of decision is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
def test_decisions_neg_delta(gcovr_test_exec: "GcovrTestExec") -> None:
    """This test case causes a negative delta value during the multiline decision analysis, which results in a:
    DecisionCoverageUncheckable: decision and a debug log
    AssertionError: assert count_false >= 0
    """
    gcovr_test_exec.cxx_link(
        "testcase",
        "-std=c++11",
        "-O0",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--verbose",
        "--decisions",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile",
        "coverage.json",
        "--txt-metric",
        "decision",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile",
        "coverage.json",
        "--decision",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()
