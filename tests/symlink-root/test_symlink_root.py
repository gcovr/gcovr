from pathlib import Path
import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """A test that verifies coverage when using symlinks to create a root directory."""
    (gcovr_test_exec.output_dir / "symlink").symlink_to(
        gcovr_test_exec.output_dir / "root"
    )
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
        cwd=Path("symlink"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("symlink"))
    gcovr_test_exec.gcovr("--txt=../coverage.txt", "--root=.", cwd=Path("symlink"))
    gcovr_test_exec.compare_txt()
