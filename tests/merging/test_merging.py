import logging
from pathlib import Path
import re
import subprocess  # nosec
import typing

import pytest


from tests.conftest import IS_LINUX, GcovrTestExec


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Merging of branches is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
def test_different_branches(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test merging different branch information for same line."""

    def outputs() -> typing.Iterable[tuple[int, Path]]:
        """Build the executables."""
        for postfix in range(1, 5):
            yield (postfix, gcovr_test_exec.output_dir / f"build{postfix}")

    for postfix, build_dir in outputs():
        build_dir.mkdir()
        additional_options = []
        if postfix in [3, 4]:
            additional_options.append("-DTWO_CONDITIONS")
        gcovr_test_exec.cxx_link(
            "testcase",
            *additional_options,
            "../main.c",
            cwd=build_dir,
        )

    gcovr_test_exec.run_parallel_from_directories(
        "./testcase",
        cwd=[build_dir for _, build_dir in outputs()],
    )
    gcovr_test_exec.gcovr(
        "--json-trace-data-source",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Merging of functions is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.parametrize(
    "merge_mode_function",
    [
        "strict",
        "merge-use-line-0",
        "merge-use-line-min",
        "merge-use-line-max",
        "separate",
    ],
)
def test_different_functions(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    caplog: pytest.LogCaptureFixture,
    check,
    merge_mode_function: str,
) -> None:
    """Test merging same function defined on different lines."""

    def outputs() -> typing.Iterable[tuple[int, Path]]:
        """Build the executables."""
        for postfix in [1, 2]:
            yield (postfix, gcovr_test_exec.output_dir / f"build{postfix}")

    for postfix, build_dir in outputs():
        build_dir.mkdir()
        additional_options = []
        if postfix == 2:
            additional_options.append("-DFOO_OTHER_LINE")
        gcovr_test_exec.cxx_link(
            "testcase",
            *additional_options,
            "../main.c",
            cwd=build_dir,
        )

    gcovr_test_exec.run_parallel_from_directories(
        "./testcase",
        cwd=[build_dir for _, build_dir in outputs()],
    )

    if merge_mode_function == "strict":
        process = gcovr_test_exec.gcovr(
            "--json-trace-data-source",
            "--json-pretty",
            "--json=coverage.json",
            use_main=True,
        )
        with check:
            assert process.returncode == 64, "Read error."
        messages = caplog.record_tuples
        with check:
            assert len(messages) == 2
            assert messages[0][1] == logging.ERROR
            for line in messages[0][2].splitlines():
                if re.match(
                    r"gcovr.exceptions.GcovrMergeAssertionError: .+func.h:5 Got function .*foo.* on multiple lines: 3, 5\.",
                    line,
                ):
                    break
            else:
                raise AssertionError("Missing expected output.")
    else:
        additional_options = [f"--merge-mode-functions={merge_mode_function}"]
        gcovr_test_exec.gcovr(
            "--verbose",
            *additional_options,
            "--json-pretty",
            "--json=coverage.json",
        )
        gcovr_test_exec.compare_json()

        if merge_mode_function == "separate":
            # Test exitcode for merging JSON with strict mode
            with pytest.raises(subprocess.CalledProcessError) as exception:
                gcovr_test_exec.gcovr(
                    "--json-add-tracefile=coverage.json",
                    "--json-pretty",
                    "--json=coverage.error.json",
                )
            assert exception.value.returncode == 64, "Read error."
        else:
            additional_options.clear()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            *additional_options,
            "--html-details=coverage.html",
        )
        gcovr_test_exec.compare_html()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            *additional_options,
            "--txt=coverage.txt",
        )
        gcovr_test_exec.compare_txt()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            *additional_options,
            "--cobertura-pretty",
            "--cobertura=cobertura.xml",
        )
        gcovr_test_exec.compare_cobertura()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            *additional_options,
            "--coveralls-pretty",
            "--coveralls=coveralls.json",
        )
        gcovr_test_exec.compare_coveralls()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            *additional_options,
            "--lcov=coverage.lcov",
        )
        gcovr_test_exec.compare_lcov()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            *additional_options,
            "--sonarqube=sonarqube.xml",
        )
        gcovr_test_exec.compare_sonarqube()
