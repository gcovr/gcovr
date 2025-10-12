import logging
import re
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec", caplog: pytest.LogCaptureFixture) -> None:
    """Test a gcovr worker exception."""

    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("testcase")
    process = gcovr_test_exec.gcovr(
        "--gcov-executable=./gcov-stub",
        "--txt=coverage.txt",
        use_main=True,
    )
    assert process.returncode == 64
    messages = caplog.record_tuples
    assert len(messages) == 2
    assert messages[0][1] == logging.ERROR
    assert re.fullmatch(
        r"AssertionError: Sanity check failed, output file .+does#not#exist.gcov doesn't exist but no error from GCOV detected.",
        messages[0][2].splitlines()[-1],
    )
    assert messages[1][1] == logging.ERROR
    assert (
        messages[1][2].splitlines()[-1]
        == "RuntimeError: Worker thread raised exception, workers canceled."
    )
    caplog.clear()

    assert not (gcovr_test_exec.output_dir / "coverage.txt").exists(), (
        "No output file must be written."
    )
