import os
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    "GCOVR_ISOLATED_TEST" not in os.environ,
    reason="Only available in isolated docker test.",
)
def test_gtest(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test cmake with gtest."""
    for file in (gcovr_test_exec.output_dir / "gtest").glob("*"):
        file.rename(gcovr_test_exec.output_dir / file.name)
    gcovr_test_exec.run(
        "cmake",
        "-G",
        "Ninja",
        "-DCMAKE_BUILD_TYPE=PROFILE",
        "-S",
        ".",
        "-B",
        gcovr_test_exec.output_dir,
    )
    gcovr_test_exec.run("cmake", "--build", gcovr_test_exec.output_dir, "--", "-v")

    gcovr_test_exec.run(
        gcovr_test_exec.output_dir / "gcovr_gtest",
        cwd=gcovr_test_exec.output_dir,
    )
    gcovr_test_exec.gcovr(
        "--filter",
        "source/",
        "--json-pretty",
        "--json=coverage.json",
        "--gcov-object-directory",
        gcovr_test_exec.output_dir,
    )
    gcovr_test_exec.compare_json()


def test_oos_makefile(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test CMake out of source build with makefile."""
    for file in (gcovr_test_exec.output_dir / "simple_main").glob("*"):
        file.rename(gcovr_test_exec.output_dir / file.name)
    build_dir = gcovr_test_exec.output_dir / "build"
    build_dir.mkdir()
    generator = "MSYS Makefiles" if gcovr_test_exec.is_windows() else "Unix Makefiles"
    gcovr_test_exec.run(
        "cmake",
        "-G",
        generator,
        "-DCMAKE_BUILD_TYPE=PROFILE",
        "..",
        cwd=build_dir,
    )
    gcovr_test_exec.run(
        "make",
        cwd=build_dir,
    )

    gcovr_test_exec.run(
        build_dir / "testcase",
        cwd=build_dir,
    )
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()


def test_oos_ninja(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test CMake out of source build with ninja."""
    for file in (gcovr_test_exec.output_dir / "simple_main").glob("*"):
        file.rename(gcovr_test_exec.output_dir / file.name)
    build_dir = gcovr_test_exec.output_dir / "build"
    build_dir.mkdir()
    gcovr_test_exec.run(
        "cmake",
        "-G",
        "Ninja",
        "-DCMAKE_BUILD_TYPE=PROFILE",
        "-S",
        "..",
        "-B",
        ".",
        cwd=build_dir,
    )
    gcovr_test_exec.run("cmake", "--build", build_dir, "--", "-v")

    gcovr_test_exec.run(
        build_dir / "testcase",
        cwd=build_dir,
    )
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
