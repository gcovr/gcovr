import logging
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_report_name_with_spaces(
    gcovr_test_exec: "GcovrTestExec", caplog: pytest.LogCaptureFixture
) -> None:
    """Test error if report name contains spaces."""
    process = gcovr_test_exec.gcovr(
        "--lcov-test-name", "Name with spaces", use_main=True
    )
    assert process.returncode == 1
    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.ERROR
    assert (
        messages[0][2]
        == "The LCOV test name must not contain spaces, got 'Name with spaces'."
    )
