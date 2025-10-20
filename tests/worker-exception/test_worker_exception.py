import re
import subprocess  # nosec

import pytest

from tests.conftest import IS_WINDOWS, GcovrTestExec


@pytest.mark.skipif(IS_WINDOWS, reason="GCOV stub script sin't working under Windows")
def test(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test a gcovr worker exception."""

    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    with pytest.raises(subprocess.CalledProcessError) as exc:
        gcovr_test_exec.gcovr(
            "--verbose",
            "--gcov-executable=./gcov-stub",
            "--txt=coverage.txt",
        )

    check.equal(
        exc.value.returncode, 64, "Gcovr must return exit code 64 on worker exception."
    )
    check.is_true(
        re.search(
            r"AssertionError: Sanity check failed, output file .+does#not#exist.gcov doesn't exist but no error from GCOV detected.",
            exc.value.stderr,
        ),
        "Sanity check exception found in stderr.",
    )
    check.is_in(
        "RuntimeError: Worker thread raised exception, workers canceled.",
        exc.value.stderr,
        "Workers canceled exception found in stderr.",
    )

    check.is_false(
        (gcovr_test_exec.output_dir / "coverage.txt").exists(),
        "No output file must be written.",
    )
