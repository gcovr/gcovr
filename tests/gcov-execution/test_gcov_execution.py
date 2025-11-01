from contextlib import contextmanager
from pathlib import Path
import subprocess  # nosec
import typing

import pytest

from tests.conftest import (
    GCOVR_ISOLATED_TEST,
    IS_DARWIN_HOST,
    USE_GCC_JSON_INTERMEDIATE_FORMAT,
    GcovrTestExec,
)


CHMOD_IS_WORKING = (
    not GCOVR_ISOLATED_TEST or IS_DARWIN_HOST or USE_GCC_JSON_INTERMEDIATE_FORMAT
)


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
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
def test_wd_not_found(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test working directory not found."""

    (gcovr_test_exec.output_dir / "build").mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_test_exec.is_darwin() else 0o555,
        gcovr_test_exec.output_dir / "src",
        gcovr_test_exec.output_dir / "build",
    ):
        with pytest.raises(subprocess.CalledProcessError) as exc:
            gcovr_test_exec.gcovr(
                "--verbose",
                "--json-pretty",
                "--json=coverage.json",
                "--root=src",
                "build",
            )
        assert exc.value.returncode == 64
        check.is_in(
            "GCOV could not write output file, this can be ignored with --gcov-ignore-errors=output_error.",
            exc.value.stderr,
        )
        check.is_in(
            "GCOV could not find source file, this can be ignored with --gcov-ignore-errors=source_not_found.",
            exc.value.stderr,
        )
        check.is_in(
            "GCOVR could not infer a working directory that resolved it.",
            exc.value.stderr,
        )
        check.is_in(
            "To ignore this error use option --gcov-ignore-errors=no_working_dir_found.",
            exc.value.stderr,
        )


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
def test_ignore_output_error(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test ignoring GCOV output errors."""

    (gcovr_test_exec.output_dir / "build").mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_test_exec.is_darwin() else 0o555,
        gcovr_test_exec.output_dir / "src",
        gcovr_test_exec.output_dir / "build",
    ):
        process = gcovr_test_exec.gcovr(
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--gcov-ignore-errors=output_error",
            "--root=src",
            "build",
        )
        check.is_not_in(
            "GCOV could not write output file, this can be ignored with --gcov-ignore-errors=output_error.",
            process.stderr,
        )
        check.is_not_in(
            "GCOV could not find source file, this can be ignored with --gcov-ignore-errors=source_not_found.",
            process.stderr,
        )
        check.is_not_in(
            "GCOVR could not infer a working directory that resolved it.",
            process.stderr,
        )
    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
def test_ignore_source_not_found(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test ignoring GCOV source not found errors."""

    (gcovr_test_exec.output_dir / "build").mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_test_exec.is_darwin() else 0o555,
        gcovr_test_exec.output_dir / "src",
        gcovr_test_exec.output_dir / "build",
    ):
        process = gcovr_test_exec.gcovr(
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--gcov-ignore-errors=source_not_found",
            "--root=src",
            "build",
        )
        check.is_not_in(
            "GCOV could not write output file, this can be ignored with --gcov-ignore-errors=output_error.",
            process.stderr,
        )
        check.is_not_in(
            "GCOV could not find source file, this can be ignored with --gcov-ignore-errors=source_not_found.",
            process.stderr,
        )
        check.is_not_in(
            "GCOVR could not infer a working directory that resolved it.",
            process.stderr,
        )
    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
def test_ignore_no_working_dir_found(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test gcov-no_working_dir_found logic."""

    (gcovr_test_exec.output_dir / "build").mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("build"))

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
        process = gcovr_test_exec.gcovr(*gcovr_args)
        check.is_not_in(
            "GCOV could not write output file, this can be ignored with --gcov-ignore-errors=output_error.",
            process.stderr,
        )
        check.is_not_in(
            "GCOV could not find source file, this can be ignored with --gcov-ignore-errors=source_not_found.",
            process.stderr,
        )
        check.is_not_in(
            "GCOVR could not infer a working directory that resolved it.",
            process.stderr,
        )
    gcovr_test_exec.compare_json()
