# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2022 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import glob
import os
import platform
import shutil
import shlex
import sys
import nox

GCC_VERSIONS = [
    "gcc-5",
    "gcc-6",
    "gcc-8",
    "gcc-9",
    "gcc-10",
    "gcc-11",
    "clang-10",
    "clang-13",
]
GCC_VERSION2USE = os.path.split(os.environ.get("CC", "gcc-5"))[1]
DEFAULT_TEST_DIRECTORIES = ["doc", "gcovr"]
DEFAULT_LINT_ARGUMENTS = ["setup.py", "noxfile.py", "admin"] + DEFAULT_TEST_DIRECTORIES

BLACK_PINNED_VERSION = "black==22.3.0"

nox.options.sessions = ["qa"]


def set_environment(session: nox.Session, cc: str, check: bool = True) -> None:
    if check and (shutil.which(cc) is None):
        session.env["CC_REFERENCE"] = cc
        cc = "gcc"
    cxx = cc.replace("clang", "clang++").replace("gcc", "g++")
    session.env["GCOVR_TEST_SUITE"] = "1"
    session.env["CC"] = cc
    session.env["CFLAGS"] = "--this_flag_does_not_exist"
    session.env["CXX"] = cxx
    session.env["CXXFLAGS"] = "--this_flag_does_not_exist"


@nox.session(python=False)
def qa(session: nox.Session) -> None:
    """Run the quality tests for the default GCC version."""
    session_id = f"qa_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def qa_compiler(session: nox.Session, version: str) -> None:
    """Run the quality tests for a specific GCC version."""
    session_id = "lint"
    session.log(f"Notify session {session_id}")
    session.notify(session_id, [])
    session_id = "doc"
    session.log(f"Notify session {session_id}")
    session.notify(session_id, [])
    session_id = f"tests_compiler({version})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session
def lint(session: nox.Session) -> None:
    """Run the lint (flake8 and black)."""
    session.install("flake8", "flake8-print")
    # Black installs under Pypy but doesn't necessarily run (cf psf/black#2559).
    if platform.python_implementation() == "CPython":
        session.install(BLACK_PINNED_VERSION)
    if session.posargs:
        args = session.posargs
    else:
        args = DEFAULT_LINT_ARGUMENTS
    session.run("flake8", *args)

    if platform.python_implementation() == "CPython":
        session.run("python", "-m", "black", "--diff", "--check", *args)
    else:
        session.log(
            f"Skip black because of platform {platform.python_implementation()}."
        )


@nox.session
def black(session: nox.Session) -> None:
    """Run black, a code formatter and format checker."""
    session.install(BLACK_PINNED_VERSION)
    if session.posargs:
        session.run("python", "-m", "black", *session.posargs)
    else:
        session.run("python", "-m", "black", *DEFAULT_LINT_ARGUMENTS)


@nox.session
def doc(session: nox.Session) -> None:
    """Generate the documentation."""
    session.install("-r", "doc/requirements.txt", "docutils")
    session.install("-e", ".")

    # Build the Sphinx documentation
    session.chdir("doc")
    session.run("make", "html", "O=-W", external=True)
    session.chdir("..")

    # Ensure that the README builds fine as a standalone document.
    readme_html = session.create_tmp() + "/README.html"
    session.run("rst2html5.py", "--strict", "README.rst", readme_html)


@nox.session(python=False)
def tests(session: nox.Session) -> None:
    """Run the tests with the default GCC version."""
    session_id = f"tests_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="tests_compiler(all)")
def tests_compiler_all(session: nox.Session) -> None:
    """Run the tests with all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"tests_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def tests_compiler(session: nox.Session, version: str) -> None:
    """Run the test with a specifiv GCC version."""
    session.install(
        "jinja2",
        "lxml",
        "pygments==2.7.4",
        "pytest",
        "pytest-timeout",
        "cmake",
        "yaxmldiff",
    )
    if platform.system() == "Windows":
        session.install("pywin32")
    coverage_args = []
    if os.environ.get("USE_COVERAGE") == "true":
        session.install("pytest-cov")
        coverage_args = ["--cov=gcovr", "--cov-branch"]
    session.install("-e", ".")
    set_environment(session, version)
    session.log("Print tool versions")
    session.run("python", "--version")
    # Use full path to executable
    session.env["CC"] = shutil.which(session.env["CC"]).replace(os.path.sep, "/")
    session.run(session.env["CC"], "--version", external=True)
    session.env["CXX"] = shutil.which(session.env["CXX"]).replace(os.path.sep, "/")
    session.run(session.env["CXX"], "--version", external=True)
    session.env["GCOV"] = shutil.which(
        session.env["CC"].replace("clang", "llvm-cov").replace("gcc", "gcov")
    ).replace(os.path.sep, "/")
    session.run(session.env["GCOV"], "--version", external=True)
    if "llvm-cov" in session.env["GCOV"]:
        session.env["GCOV"] += " gcov"

    session.chdir("gcovr/tests")
    session.run("make", "--silent", "clean", external=True)
    session.chdir("../..")
    args = ["-m", "pytest"]
    args += coverage_args
    args += session.posargs
    # For docker tests
    if "NOX_POSARGS" in os.environ:
        args += shlex.split(os.environ["NOX_POSARGS"])
    if "--" not in args:
        args += ["--"] + DEFAULT_TEST_DIRECTORIES
    session.run("python", *args)


@nox.session
def build_wheel(session: nox.Session) -> None:
    """Build a wheel."""
    session.install("wheel")
    session.run("python", "setup.py", "sdist", "bdist_wheel")
    dist_cache = f"{session.cache_dir}/dist"
    if os.path.isdir(dist_cache):
        shutil.rmtree(dist_cache)
    shutil.copytree("dist", dist_cache)
    session.notify("check_wheel")


@nox.session
def check_wheel(session: nox.Session) -> None:
    """Check the wheel, should not be used directly."""
    session.install("wheel", "twine")
    session.chdir(f"{session.cache_dir}/dist")
    session.run("twine", "check", "*", external=True)
    session.install(glob.glob("*.whl")[0])
    session.run("python", "-m", "gcovr", "--help", external=True)


@nox.session
def upload_wheel(session: nox.Session) -> None:
    """Upload the wheel."""
    session.install("twine")
    session.run("twine", "upload", "dist/*", external=True)


def docker_container_os(session: nox.Session) -> str:
    if session.env["CC"] in ["gcc-5", "gcc-6"]:
        return "ubuntu:18.04"
    elif session.env["CC"] in ["gcc-8", "gcc-9", "clang-10"]:
        return "ubuntu:20.04"
    return "ubuntu:22.04"


def docker_container_id(session: nox.Session, version: str) -> str:
    """Get the docker container ID."""
    return f"gcovr-qa-{docker_container_os(session).replace(':', '_')}-{version}-uid_{os.geteuid()}"


@nox.session(python=False)
def docker_qa_build(session: nox.Session) -> None:
    """Build the docker container for the default GCC version."""
    session_id = f"docker_qa_build({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_qa_build_compiler(all)")
def docker_qa_build_compiler_all(session: nox.Session) -> None:
    """Build the docker containers vor all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_qa_build_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_build_compiler(session: nox.Session, version: str) -> None:
    """Build the docker container for a specific GCC version."""
    set_environment(session, version, False)
    session.run(
        "docker",
        "build",
        "--tag",
        docker_container_id(session, version),
        "--build-arg",
        f"DOCKER_OS={docker_container_os(session)}",
        "--build-arg",
        f"USERID={os.geteuid()}",
        "--build-arg",
        f"CC={session.env['CC']}",
        "--build-arg",
        f"CXX={session.env['CXX']}",
        "--file",
        "admin/Dockerfile.qa",
        ".",
        external=True,
    )


@nox.session(python=False)
def docker_qa_run(session: nox.Session) -> None:
    """Run the docker container for the default GCC version."""
    session_id = f"docker_qa_run_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_qa_run_compiler(all)")
def docker_qa_run_compiler_all(session: nox.Session) -> None:
    """Run the docker container for the all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_qa_run_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_run_compiler(session: nox.Session, version: str) -> None:
    """Run the docker container for a specific GCC version."""
    set_environment(session, version, False)

    def shell_join(args):
        if sys.version_info >= (3, 8):
            return shlex.join(args)
        else:
            # Code for join taken from Python 3.9
            return " ".join(shlex.quote(arg) for arg in args)

    session.env["NOX_POSARGS"] = shell_join(session.posargs)
    nox_options = []
    if session._runner.global_config.no_install:
        nox_options.append("--no-install")
    if session._runner.global_config.reuse_existing_virtualenvs:
        nox_options.append("--reuse-existing-virtualenvs")
    session.env["NOX_OPTIONS"] = shell_join(nox_options)
    session.run(
        "docker",
        "run",
        "--rm",
        "-e",
        "CC",
        "-e",
        "NOX_POSARGS",
        "-e",
        "NOX_OPTIONS",
        "-v",
        f"{os.getcwd()}:/gcovr",
        docker_container_id(session, version),
        external=True,
    )


@nox.session(python=False)
def docker_qa(session: nox.Session) -> None:
    """Build and run the docker container for the default GCC version."""
    session_id = f"docker_qa_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_qa_compiler(all)")
def docker_qa_compiler_all(session: nox.Session) -> None:
    """Build and run the docker container for the all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_qa_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_compiler(session: nox.Session, version: str) -> None:
    """Build and run the docker container for a specific GCC version."""
    session_id = "docker_qa_build_compiler({})".format(version)
    session.log(f"Notify session {session_id}")
    session.notify(session_id)
    session_id = f"docker_qa_run_compiler({version})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)
