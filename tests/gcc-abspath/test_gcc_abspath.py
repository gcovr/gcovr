import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test gcc-abspath coverage."""
    needed_option = "-fprofile-abs-path"
    if gcovr_test_exec.is_in_gcc_help(needed_option):
        subfolder = gcovr_test_exec.output_dir / "subfolder"
        gcovr_test_exec.cc_link(
            "testcase",
            needed_option,
            "main.c",
            cwd=subfolder,
        )

        gcovr_test_exec.run("./testcase", cwd=subfolder)
        for file in subfolder.glob("*.gc??"):
            file.rename(file.parent.parent / file.name)
        gcovr_test_exec.gcovr("-d", "--json-pretty", "--json=coverage.json")
        gcovr_test_exec.compare_json()
