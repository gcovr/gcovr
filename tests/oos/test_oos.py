import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_oos_1(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test out-of-source build and coverage."""
    build_dir = gcovr_test_exec.output_dir / "build"
    build_dir.mkdir()
    gcovr_test_exec.cxx_link(
        "build/testcase",
        gcovr_test_exec.cxx_compile("src/file1.cpp", target="build/file1.o"),
        gcovr_test_exec.cxx_compile("src/main.cpp", target="build/main.o"),
    )

    gcovr_test_exec.run("./build/testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()


def test_oos_2(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test out-of-source build and coverage."""
    build_dir = gcovr_test_exec.output_dir / "build"
    build_dir.mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile(
            "../src/file1.cpp", target="file1.o", cwd=build_dir
        ),
        gcovr_test_exec.cxx_compile("../src/main.cpp", target="main.o", cwd=build_dir),
        cwd=build_dir,
    )

    gcovr_test_exec.run("./build/testcase")
    gcovr_test_exec.gcovr(
        "-r",
        "../src",
        "--json-pretty",
        "--json",
        "../coverage.json",
        ".",
        cwd=build_dir,
    )
    gcovr_test_exec.compare_json()
