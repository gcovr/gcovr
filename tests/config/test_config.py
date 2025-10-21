import logging
from pathlib import Path
import shutil
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_config_error(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test config with wrong value."""
    gcovr_config = Path("config", "gcovr.error.config")
    with pytest.raises(ValueError) as exception:
        gcovr_test_exec.gcovr(
            f"--config={gcovr_config}",
            use_main=True,
        )

    assert str(exception.value).startswith(
        f"{gcovr_config}: 1: gcov-ignore-parse-errors: must be one of"
    )


def test_config_deprecated(
    gcovr_test_exec: "GcovrTestExec", caplog: "pytest.LogCaptureFixture"
) -> None:
    """Test config with deprecated key."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--config=config/gcovr.deprecated.config",
        use_main=True,
    )

    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.WARNING
    assert (
        messages[0][2]
        == "Deprecated config key txt-branch used, please use 'txt-metric=branch' instead."
    )


def test_gcovr_config(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test JSON output with gcovr.config."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--config=config/gcovr.json.config",
    )
    gcovr_test_exec.compare_json()


def test_pyproject_toml(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test JSON output with pyproject.toml."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    shutil.copy(
        gcovr_test_exec.output_dir / "config" / "pyproject.toml",
        gcovr_test_exec.output_dir / "pyproject.toml",
    )
    gcovr_test_exec.gcovr()
    gcovr_test_exec.compare_json()


def test_gcovr_toml(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test JSON output with gcovr.toml."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    (gcovr_test_exec.output_dir / "gcovr.toml").write_text(
        "".join(
            line
            for line in (gcovr_test_exec.output_dir / "config" / "pyproject.toml")
            .read_text(encoding="utf-8")
            .splitlines(keepends=True)
            if "[tool.gcovr]" not in line
        ),
        encoding="utf-8",
    )
    gcovr_test_exec.gcovr()
    gcovr_test_exec.compare_json()
