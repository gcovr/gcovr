#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.7+main, a parsing and reporting tool for gcov.
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

import os
import typing
from pathlib import Path

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture


def outputs(
    gcovr_exec: "GcovrExecFixture",
) -> typing.Generator[tuple[str, Path], None, None]:
    """Yield the output directories."""
    for postfix in ["a", "b", "c"]:
        yield (postfix, gcovr_exec.output_dir / f"build.{postfix}")


def build(gcovr_exec: "GcovrExecFixture") -> None:
    """Build the executables."""
    for postfix, build_dir in outputs(gcovr_exec):
        build_dir.mkdir()
        gcovr_exec.run(
            "cmake",
            "-G",
            "Ninja",
            "-DCMAKE_BUILD_TYPE=PROFILE",
            "-S",
            ".",
            "-B",
            build_dir,
            "-D",
            f"ODD={'OFF' if postfix == 'b' else 'ON'}",
        )
        gcovr_exec.run("cmake", "--build", build_dir, "--", "-v")


def run(gcovr_exec: "GcovrExecFixture") -> None:
    """Run the executables."""
    gcovr_exec.run_parallel_from_directories(
        "./parallel_call",
        cwd=[build_dir for _, build_dir in outputs(gcovr_exec)],
    )


def report(gcovr_exec: "GcovrExecFixture") -> None:
    """Generate the reports."""
    for postfix, _ in outputs(gcovr_exec):
        gcovr_exec.gcovr(
            "--json-add-tracefile",
            f"coverage.{postfix}.json",
            "--txt",
            f"coverage.{postfix}.txt",
        )
    gcovr_exec.compare_txt()

    for postfix, _ in outputs(gcovr_exec):
        gcovr_exec.gcovr(
            "--json-add-tracefile",
            f"coverage.{postfix}.json",
            "--cobertura-pretty",
            "--cobertura",
            f"cobertura.{postfix}.xml",
        )
    gcovr_exec.compare_cobertura()

    for postfix, _ in outputs(gcovr_exec):
        gcovr_exec.gcovr(
            "--json-add-tracefile",
            f"coverage.{postfix}.json",
            "--coveralls-pretty",
            "--coveralls",
            f"coveralls.{postfix}.json",
            use_main=False,
        )
    gcovr_exec.compare_coveralls()

    for postfix, _ in outputs(gcovr_exec):
        gcovr_exec.gcovr(
            "--json-add-tracefile",
            f"coverage.{postfix}.json",
            "--sonarqube",
            f"sonarqube.{postfix}.xml",
        )
    gcovr_exec.compare_sonarqube()


@pytest.mark.json
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.sonarqube
@pytest.mark.txt
def test_from_build_dir(gcovr_exec: "GcovrExecFixture") -> None:
    """Test calling from build directory."""
    build(gcovr_exec)
    run(gcovr_exec)
    for postfix, build_dir in outputs(gcovr_exec):
        gcovr_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_exec.output_dir / f"coverage.{postfix}.json",
            "--object-directory",
            build_dir,
            "--root",
            gcovr_exec.output_dir,
            build_dir,
            cwd=build_dir,
        )
    gcovr_exec.compare_json()

    report(gcovr_exec)


@pytest.mark.json
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.sonarqube
@pytest.mark.txt
def test_from_build_dir_without_object_dir(gcovr_exec: "GcovrExecFixture") -> None:
    """Test calling from build directory without object directory."""
    build(gcovr_exec)
    run(gcovr_exec)

    for postfix, build_dir in outputs(gcovr_exec):
        gcovr_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_exec.output_dir / f"coverage.{postfix}.json",
            "--root",
            gcovr_exec.output_dir,
            build_dir,
            cwd=build_dir,
        )
    gcovr_exec.compare_json()

    report(gcovr_exec)


@pytest.mark.json
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.sonarqube
@pytest.mark.txt
def test_from_build_dir_without_search_dir(gcovr_exec: "GcovrExecFixture") -> None:
    """Test calling from build directory without search directory."""
    build(gcovr_exec)
    run(gcovr_exec)

    for postfix, build_dir in outputs(gcovr_exec):
        env = os.environ.copy()
        env.update(
            {
                "GCOV_STRIP": "99",
                "GCOV_PREFIX": str(build_dir),
            },
        )
        gcovr_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_exec.output_dir / f"coverage.{postfix}.json",
            "--object-directory",
            build_dir,
            "--root",
            gcovr_exec.output_dir,
            cwd=build_dir,
            env=env,
        )
    gcovr_exec.compare_json()

    report(gcovr_exec)


@pytest.mark.json
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.sonarqube
@pytest.mark.txt
def test_from_root_dir(gcovr_exec: "GcovrExecFixture") -> None:
    """Test calling from root directory."""
    build(gcovr_exec)
    run(gcovr_exec)
    for postfix, build_dir in outputs(gcovr_exec):
        gcovr_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_exec.output_dir / f"coverage.{postfix}.json",
            "--object-directory",
            build_dir,
            build_dir,
        )
    gcovr_exec.compare_json()

    report(gcovr_exec)


@pytest.mark.json
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.sonarqube
@pytest.mark.txt
def test_from_root_dir_without_object_dir(gcovr_exec: "GcovrExecFixture") -> None:
    """Test calling from root directory without object directory."""
    build(gcovr_exec)
    run(gcovr_exec)

    for postfix, build_dir in outputs(gcovr_exec):
        gcovr_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_exec.output_dir / f"coverage.{postfix}.json",
            build_dir,
        )
    gcovr_exec.compare_json()

    report(gcovr_exec)


@pytest.mark.json
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.sonarqube
@pytest.mark.txt
def test_from_root_dir_without_search_dir(gcovr_exec: "GcovrExecFixture") -> None:
    """Test calling from root directory without search directory."""
    build(gcovr_exec)
    run(gcovr_exec)

    for postfix, build_dir in outputs(gcovr_exec):
        env = os.environ.copy()
        env.update(
            {
                "GCOV_STRIP": "99",
                "GCOV_PREFIX": str(build_dir),
            },
        )
        gcovr_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_exec.output_dir / f"coverage.{postfix}.json",
            "--object-directory",
            build_dir,
            env=env,
        )
    gcovr_exec.compare_json()

    report(gcovr_exec)
