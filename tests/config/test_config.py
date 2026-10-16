#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.7, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.7
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import logging
import re
import shutil
import typing
from pathlib import Path

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture


def test_config_error(gcovr_exec: "GcovrExecFixture") -> None:
    """Test config with wrong value."""
    gcovr_config = Path("config", "gcovr.error.config")
    with pytest.raises(
        ValueError,
        match=rf"{re.escape(str(gcovr_config))}: 1: gcov-ignore-parse-errors: must be one of",
    ):
        gcovr_exec.gcovr(
            f"--config={gcovr_config}",
        )


def test_config_deprecated(
    gcovr_exec: "GcovrExecFixture", caplog: "pytest.LogCaptureFixture"
) -> None:
    """Test config with deprecated key."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--config=config/gcovr.deprecated.config",
    )

    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.WARNING
    assert (
        messages[0][2]
        == "Deprecated config key sort-percentage used, please use 'sort=uncovered-percent' instead."
    )


@pytest.mark.json
@pytest.mark.txt
def test_gcovr_config(gcovr_exec: "GcovrExecFixture") -> None:
    """Test JSON output with gcovr.config."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--config=config/gcovr.config",
    )
    gcovr_exec.compare_json()
    gcovr_exec.compare_txt()


@pytest.mark.json
@pytest.mark.txt
def test_pyproject_toml(gcovr_exec: "GcovrExecFixture") -> None:
    """Test JSON output with pyproject.toml."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
    )

    gcovr_exec.run("./testcase")
    shutil.copy(
        gcovr_exec.output_dir / "config" / "pyproject.toml",
        gcovr_exec.output_dir / "pyproject.toml",
    )
    gcovr_exec.gcovr()
    gcovr_exec.compare_json()
    gcovr_exec.compare_txt()


@pytest.mark.json
@pytest.mark.txt
def test_gcovr_toml(gcovr_exec: "GcovrExecFixture") -> None:
    """Test JSON output with gcovr.toml."""
    gcovr_exec.cxx_link(
        "testcase",
        gcovr_exec.cxx_compile("main.cpp"),
    )

    gcovr_exec.run("./testcase")
    (gcovr_exec.output_dir / "gcovr.toml").write_text(
        "".join(
            line
            for line in (gcovr_exec.output_dir / "config" / "pyproject.toml")
            .read_text(encoding="utf-8")
            .splitlines(keepends=True)
            if "[tool.gcovr]" not in line
        ),
        encoding="utf-8",
    )
    gcovr_exec.gcovr()
    gcovr_exec.compare_json()
    gcovr_exec.compare_txt()
