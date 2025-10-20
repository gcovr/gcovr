from pathlib import Path
import platform
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def outputs(gcovr_test_exec: "GcovrTestExec") -> typing.Iterable[tuple[int, Path]]:
    """Build the executables."""
    for postfix in range(1, 5):
        yield (postfix, gcovr_test_exec.output_dir / f"build{postfix}")


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Merging of branches is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test merging different branch information for same line."""
    for postfix, build_dir in outputs(gcovr_test_exec):
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
        cwd=[build_dir for _, build_dir in outputs(gcovr_test_exec)],
    )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--gcov-keep",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
