from contextlib import contextmanager
from pathlib import Path
import platform
import typing

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@contextmanager
def chmod(mode: int, *paths: Path) -> typing.Iterator[None]:
    """Change mode during execution."""
    modes = []
    try:
        for path in paths:
            modes.append(path.stat().st_mode)
            path.chmod(mode)
        yield
    finally:
        for index, mode in enumerate(modes):
            paths[index].chmod(mode)


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Setting write protection on directory has no effect on Windows systems.",
)
def test_ignore_output_error(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test ignoring GCOV output errors."""

    (gcovr_test_exec.output_dir / "build").mkdir()
    gcovr_test_exec.cxx_link(
        "build/testcase", gcovr_test_exec.cxx_compile("src/main.cpp")
    )

    gcovr_test_exec.run("./build/testcase")
    with chmod(
        0o455 if gcovr_test_exec.is_darwin() else 0o555,
        gcovr_test_exec.output_dir / "src",
        gcovr_test_exec.output_dir / "build",
    ):
        gcovr_test_exec.gcovr(
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--gcov-ignore-errors=output_error",
            "--root",
            "src",
            "build",
        )
    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Setting write protection on directory has no effect on Windows systems.",
)
def test_no_working_dir_found(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test gcov-no_working_dir_found logic."""

    (gcovr_test_exec.output_dir / "build").mkdir()
    gcovr_test_exec.cxx_link(
        "build/testcase", gcovr_test_exec.cxx_compile("src/main.cpp")
    )

    gcovr_test_exec.run("./build/testcase")
    with chmod(
        0o455 if gcovr_test_exec.is_darwin() else 0o555,
        gcovr_test_exec.output_dir / "src",
        gcovr_test_exec.output_dir / "build",
    ):
        gcovr_args = [
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--root=src",
            "build",
        ]
        if not gcovr_test_exec.use_gcc_json_format():
            gcovr_args.insert(0, "--gcov-ignore-errors=no_working_dir_found")
        gcovr_test_exec.gcovr(*gcovr_args)
    gcovr_test_exec.compare_json()
