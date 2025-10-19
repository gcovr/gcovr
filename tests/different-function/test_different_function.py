import logging
from pathlib import Path
import platform
import re
import subprocess  # nosec
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def outputs(gcovr_test_exec: "GcovrTestExec") -> typing.Iterable[tuple[int, Path]]:
    """Build the executables."""
    for postfix in [1, 2]:
        yield (postfix, gcovr_test_exec.output_dir / f"build{postfix}")


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Merging of functions is independent of OS and we do not want to have separate data wor Windows and Darwin.",
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
def test(
    gcovr_test_exec: "GcovrTestExec",
    merge_mode_function: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test merging same function defined on different lines."""
    for postfix, build_dir in outputs(gcovr_test_exec):
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
        cwd=[build_dir for _, build_dir in outputs(gcovr_test_exec)],
    )

    if merge_mode_function == "strict":
        process = gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json=coverage.json",
            "--gcov-keep",
            use_main=True,
        )
        assert process.returncode == 64, "Read error."
        messages = caplog.record_tuples
        assert len(messages) == 2
        assert messages[0][1] == logging.ERROR
        for line in messages[0][2].splitlines():
            if re.match(
                r"gcovr.data_model.coverage.GcovrMergeAssertionError: .+func.h:5 Got function .*foo.* on multiple lines: 3, 5\.",
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
                    "--json-add-tracefile",
                    "coverage.json",
                    "--json-pretty",
                    "--json",
                    "coverage.error.json",
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
