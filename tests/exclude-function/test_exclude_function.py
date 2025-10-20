import platform
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Exclusion markers are independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test excluding of functions."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "--exclude-function",
        "sort_excluded_both()::{lambda(int, int)#2}::operator()(int, int) const",
        "--exclude-function",
        "/bar.+/",
        "--json-pretty",
        "--json=coverage.json",
    )
    coverage_json_content = (gcovr_test_exec.output_dir / "coverage.json").read_text(
        encoding="utf-8"
    )
    if '"pos"' in coverage_json_content:
        for pos in ["9:8", "50:19"]:
            with check:
                assert (
                    f"Function exclude marker found on line {pos} but no function definition found"
                    in process.stderr
                )

        def assert_stderr(string: str) -> None:
            assert string not in process.stderr
    else:

        def assert_stderr(string: str) -> None:
            assert string in process.stderr

    positions = ["9:8", "50:19"]
    if gcovr_test_exec.is_cxx_lambda_expression_available():
        positions += ["44:29", "50:19", "57:29", "66:34", "73:29"]
    for pos in positions:
        with check:
            assert_stderr(
                f"Function exclude marker found on line {pos} but not supported for this compiler"
            )

    gcovr_test_exec.compare_json()
