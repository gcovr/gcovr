# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.5+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
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

import re
import shutil
from sys import stderr
from unittest import mock

import pytest

from tests.conftest import GCOVR_ISOLATED_TEST, GcovrTestExec


@pytest.mark.skipif(
    not GCOVR_ISOLATED_TEST,
    reason="Only available in isolated docker test.",
)
@pytest.mark.json
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


@pytest.mark.json
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


@pytest.mark.skipif(
    not GCOVR_ISOLATED_TEST,
    reason="Only available in isolated docker test.",
)
@pytest.mark.json
def test_oos_makefile_ccache(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test CMake out of source build with makefile."""
    for file in (gcovr_test_exec.output_dir / "simple_main").glob("*"):
        file.rename(gcovr_test_exec.output_dir / file.name)
    build_dir = gcovr_test_exec.output_dir / "build"
    for run in range(2):
        print(f"***** Build with ccache ({run}) *****", file=stderr)
        with mock.patch.dict(
            "os.environ",
            {"CCACHE_DIR": str(gcovr_test_exec.output_dir / "ccache")},
        ):
            if build_dir.exists():
                shutil.rmtree(build_dir)
            build_dir.mkdir()
            generator = (
                "MSYS Makefiles" if gcovr_test_exec.is_windows() else "Unix Makefiles"
            )
            gcovr_test_exec.run(
                "cmake",
                "-G",
                generator,
                "-DCMAKE_BUILD_TYPE=PROFILE",
                "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache",
                "..",
                cwd=build_dir,
            )
            gcovr_test_exec.run(
                "make",
                cwd=build_dir,
            )
            process = gcovr_test_exec.run("ccache", "--show-stats", cwd=build_dir)
            rate = 0 if run == 0 else 100
            check.is_true(
                re.search(
                    rf"(?:cache hit rate\s+{rate}.00 %|Hits:.+\(\s*{rate}.0{'' if rate else '0'}\s*%\))",
                    process.stdout,
                )
            )
            gcovr_test_exec.run("ccache", "--zero-stats", cwd=build_dir)

            gcovr_test_exec.run(
                build_dir / "testcase",
                cwd=build_dir,
            )
            gcovr_test_exec.gcovr(
                "--json-pretty",
                f"--json=coverage{'' if run == 0 else '.cached'}.json",
            )
    gcovr_test_exec.run("diff", "-U", "1", "coverage.json", "coverage.cached.json")
    gcovr_test_exec.compare_json()


@pytest.mark.json
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


@pytest.mark.skipif(
    not GCOVR_ISOLATED_TEST,
    reason="Only available in isolated docker test.",
)
@pytest.mark.json
def test_oos_ninja_ccache(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test CMake out of source build with ninja."""
    for file in (gcovr_test_exec.output_dir / "simple_main").glob("*"):
        file.rename(gcovr_test_exec.output_dir / file.name)
    build_dir = gcovr_test_exec.output_dir / "build"
    for run in range(2):
        print(f"***** Build with ccache ({run}) *****", file=stderr)
        with mock.patch.dict(
            "os.environ",
            {"CCACHE_DIR": str(gcovr_test_exec.output_dir / "ccache")},
        ):
            if build_dir.exists():
                shutil.rmtree(build_dir)
            build_dir.mkdir()
            gcovr_test_exec.run(
                "cmake",
                "-G",
                "Ninja",
                "-DCMAKE_BUILD_TYPE=PROFILE",
                "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache",
                "-S",
                "..",
                "-B",
                ".",
                cwd=build_dir,
            )
            gcovr_test_exec.run("cmake", "--build", build_dir, "--", "-v")
            process = gcovr_test_exec.run("ccache", "--show-stats", cwd=build_dir)
            rate = 0 if run == 0 else 100
            check.is_true(
                re.search(
                    rf"(?:cache hit rate\s+{rate}.00 %|Hits:.+\(\s*{rate}.0{'' if rate else '0'}\s*%\))",
                    process.stdout,
                )
            )
            gcovr_test_exec.run("ccache", "--zero-stats", cwd=build_dir)

            gcovr_test_exec.run(
                build_dir / "testcase",
                cwd=build_dir,
            )
            gcovr_test_exec.gcovr(
                "--json-pretty",
                f"--json=coverage{'' if run == 0 else '.cached'}.json",
            )
    gcovr_test_exec.run("diff", "-U", "1", "coverage.json", "coverage.cached.json")
    gcovr_test_exec.compare_json()
