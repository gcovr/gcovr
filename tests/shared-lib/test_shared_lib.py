#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
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

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture


@pytest.mark.html
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.sonarqube
@pytest.mark.txt
def test(gcovr_exec: "GcovrExecFixture") -> None:
    # Build shared library and test app

    (gcovr_exec.output_dir / "obj").mkdir()
    (gcovr_exec.output_dir / "testApp" / "test").mkdir()
    if gcovr_exec.is_windows():
        shared_lib_extension = ".dll"
        shared_lib_flags = ["-shared"]
    elif gcovr_exec.is_darwin():
        shared_lib_extension = ".dylib"
        shared_lib_flags = ["-dynamiclib", "-undefined", "dynamic_lookup"]
    else:
        shared_lib_extension = ".so"
        shared_lib_flags = ["-shared"]

    run_env = os.environ.copy()
    if gcovr_exec.is_windows():
        run_env.update(
            {
                "PATH": os.pathsep.join(
                    [
                        f"{gcovr_exec.output_dir}/lib",
                        os.environ.get("PATH", ""),
                    ]
                )
            }
        )
    else:
        run_env.update(
            {
                "LD_LIBRARY_PATH": f"{gcovr_exec.output_dir}/lib",
            }
        )

    gcovr_exec.cxx_link(
        f"lib/libs{shared_lib_extension}",
        *shared_lib_flags,
        gcovr_exec.cxx_compile("lib/lib.cpp", target="obj/lib.o"),
    )
    gcovr_exec.cxx(
        "-I../lib",
        "tmp.cpp",
        "-o",
        "test/a.out",
        "-L../lib",
        "-ls",
        cwd=gcovr_exec.output_dir / "testApp",
    )

    # Run test app and generate coverage.json
    gcovr_exec.run("sh", "-c", "testApp/test/a.out", env=run_env)
    gcovr_exec.gcovr("--json-pretty", "--json=coverage.json")

    gcovr_exec.gcovr("--json-add-tracefile=coverage.json", "--txt", "coverage.txt")
    gcovr_exec.compare_txt()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_exec.compare_cobertura()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_exec.compare_html()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube", "sonarqube.xml"
    )
    gcovr_exec.compare_sonarqube()

    gcovr_exec.gcovr("--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml")
    gcovr_exec.compare_jacoco()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
        use_main=False,
    )
    gcovr_exec.compare_coveralls()
