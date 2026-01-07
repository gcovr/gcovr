import pytest

from tests.conftest import _CC_HELP_OUTPUT, GcovrTestExec

PROFILE_ABS_PATH = "-fprofile-abs-path"


@pytest.mark.skipif(
    PROFILE_ABS_PATH not in _CC_HELP_OUTPUT,
    reason=f"GCC version does not support {PROFILE_ABS_PATH}",
)
@pytest.mark.json
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test gcc-abspath coverage."""
    subfolder = gcovr_test_exec.output_dir / "subfolder"
    gcovr_test_exec.cc_link(
        "testcase",
        PROFILE_ABS_PATH,
        "main.c",
        cwd=subfolder,
    )

    gcovr_test_exec.run("./testcase", cwd=subfolder)
    for file in subfolder.glob("*.gc??"):
        file.rename(file.parent.parent / file.name)
    gcovr_test_exec.gcovr("-d", "--json-pretty", "--json=coverage.json")
    gcovr_test_exec.compare_json()
