# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0+master, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
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
import re
import shutil
import shlex
import subprocess
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
    "clang-14",
]

GCC_VERSIONS_NEWEST_FIRST = [
    "-".join(cc)
    for cc in sorted(
        [(*cc.split("-"),) for cc in GCC_VERSIONS],
        key=lambda cc: (cc[0], int(cc[1])),
        reverse=True,
    )
]

DEFAULT_TEST_DIRECTORIES = ["doc", "gcovr"]
DEFAULT_LINT_ARGUMENTS = [
    "setup.py",
    "noxfile.py",
    "scripts",
    "admin",
] + DEFAULT_TEST_DIRECTORIES

BLACK_PINNED_VERSION = "black==22.3.0"

OUTPUT_FORMATS = [
    "cobertura",
    "coveralls",
    "csv",
    "html-details",
    "json",
    "sonarqube",
    "txt",
]

nox.options.sessions = ["qa"]


def get_gcc_version_to_use():
    # If the user explicitly set CC variable, use that directly without checks.
    cc = os.environ.get("CC")
    if cc:
        return os.path.split(cc)[1]

    # Find the first insalled compiler version we suport
    for cc in GCC_VERSIONS_NEWEST_FIRST:
        if shutil.which(cc):
            return cc

    for cc in ["gcc", "clang"]:
        output = subprocess.check_output([cc, "--version"]).decode()
        # Ignore error code since we want to find a valid executable

        # look for a line "gcc WHATEVER VERSION.WHATEVER" in output like:
        #    gcc (Ubuntu 9.4.0-1ubuntu1~20.04.1) 9.4.0
        #    Copyright (C) 2019 Free Software Foundation, Inc.
        #    This is free software; see the source for copying conditions.  There is NO
        #    warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
        search_gcc_version = re.search(r"^gcc\b.* ([0-9]+)\.\S+$", output, re.M)

        # look for a line "WHATEVER clang version VERSION.WHATEVER" in output like:
        #    Apple clang version 13.1.6 (clang-1316.0.21.2.5)
        #    Target: arm64-apple-darwin21.5.0
        #    Thread model: posix
        #    InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
        search_clang_version = re.search(r"\bclang version ([0-9]+)\.", output, re.M)

        if search_gcc_version:
            major_version = search_gcc_version.group(1)
            return f"gcc-{major_version}"
        elif search_clang_version:
            major_version = search_clang_version.group(1)
            return f"clang-{major_version}"

    raise RuntimeError(
        "Could not detect a valid compiler, you can defin one by setting the environment CC"
    )


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


@nox.session
def bump_version(session: nox.Session) -> None:
    """Bump the new version"""
    session.install("-e", ".")
    session.run("python", "admin/bump_version.py")


@nox.session(python=False)
def qa(session: nox.Session) -> None:
    """Run the quality tests for the default GCC version."""
    session_id = f"qa_compiler({get_gcc_version_to_use()})"
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


@nox.session(python=False)
def lint(session: nox.Session) -> None:
    """Run the linters."""
    if session.posargs:
        args = session.posargs
    else:
        args = DEFAULT_LINT_ARGUMENTS
    session.notify("flake8", args)

    # Black installs under Pypy but doesn't necessarily run (cf psf/black#2559).
    if platform.python_implementation() == "CPython":
        session.notify("black", ["--diff", "--check", *args])
    else:
        session.log(
            f"Skip black because of platform {platform.python_implementation()}."
        )


@nox.session
def flake8(session: nox.Session) -> None:
    """Run flake8."""
    session.install("flake8", "flake8-print")
    if session.posargs:
        args = session.posargs
    else:
        args = DEFAULT_LINT_ARGUMENTS
    session.run("flake8", *args)


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
    session_id = f"tests_compiler({get_gcc_version_to_use()})"
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
    """Run the test with a specific GCC version."""
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
        session.install("coverage", "pytest-cov")
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
    if "--" not in args:
        args += ["--"] + DEFAULT_TEST_DIRECTORIES
    session.run("python", *args)
    if os.environ.get("USE_COVERAGE") == "true":
        session.run("coverage", "xml")


@nox.session
def build_wheel(session: nox.Session) -> None:
    """Build a wheel."""
    session.install("wheel")
    session.run("python", "setup.py", "sdist", "bdist_wheel")
    dist_cache = f"{session.cache_dir}/dist"
    if os.path.isdir(dist_cache):
        shutil.rmtree(dist_cache)
    shutil.copytree("dist", dist_cache)


@nox.session
def check_wheel(session: nox.Session) -> None:
    """Check the wheel and do a smoke test, should not be used directly."""
    session.install("wheel", "twine")
    with session.chdir(f"{session.cache_dir}/dist"):
        session.run("twine", "check", "*", external=True)
        session.install(glob.glob("*.whl")[0])
    session.run("python", "-m", "gcovr", "--help", external=True)
    session.run("gcovr", "--help", external=True)
    session.log("Run all transformations to check if all the modules are packed")
    with session.chdir(session.create_tmp()):
        for format in OUTPUT_FORMATS:
            session.run("gcovr", f"--{format}", f"out.{format}", external=True)


@nox.session
def upload_wheel(session: nox.Session) -> None:
    """Upload the wheel."""
    session.install("twine")
    session.run("twine", "upload", "dist/*", external=True)


@nox.session
def bundle_app(session: nox.Session) -> None:
    """Bundle a standalone executable."""
    session.install("pyinstaller")
    session.install("-e", ".")
    os.makedirs("build", exist_ok=True)
    session.chdir("build")
    if platform.system() == "Windows":
        executable = "gcovr.exe"
    else:
        executable = "gcovr"
    session.run(
        "pyinstaller",
        "--distpath",
        ".",
        "--workpath",
        "./pyinstaller",
        "--specpath",
        "./pyinstaller",
        "--onefile",
        "--collect-all",
        "gcovr.formats",
        "-n",
        executable,
        *session.posargs,
        "../scripts/pyinstaller_entrypoint.py",
    )
    session.notify("check_bundled_app")


@nox.session
def check_bundled_app(session: nox.Session) -> None:
    """Run a smoke test with the bundled app, should not be used directly."""
    with session.chdir("build"):
        # bash here is needed to be independent from the file extension (Windows).
        session.run("bash", "-c", "./gcovr --help", external=True)
        session.log("Run all transformations to check if all the modules are packed")
        session.create_tmp()
        for format in OUTPUT_FORMATS:
            session.run(
                "bash",
                "-c",
                f"./gcovr --{format} $TMPDIR/out.{format}",
                external=True,
            )


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
def docker_build(session: nox.Session) -> None:
    """Build the docker container for the default GCC version."""
    session_id = f"docker_build({GCC_VERSIONS[0]})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_build_compiler(all)")
def docker_build_compiler_all(session: nox.Session) -> None:
    """Build the docker containers vor all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_build_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_build_compiler(session: nox.Session, version: str) -> None:
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
def docker_run(session: nox.Session) -> None:
    """Run the docker container for the default GCC version."""
    session_id = f"docker_run_compiler({GCC_VERSIONS[0]})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_run_compiler(all)")
def docker_run_compiler_all(session: nox.Session) -> None:
    """Run the docker container for the all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_run_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_run_compiler(session: nox.Session, version: str) -> None:
    """Run the docker container for a specific GCC version."""
    set_environment(session, version, False)

    def shell_join(args):
        if sys.version_info >= (3, 8):
            return shlex.join(args)
        else:
            # Code for join taken from Python 3.9
            return " ".join(shlex.quote(arg) for arg in args)

    nox_options = session.posargs
    if session._runner.global_config.no_install:
        nox_options.insert(0, "--no-install")
    if session._runner.global_config.reuse_existing_virtualenvs:
        nox_options.insert(0, "--reuse-existing-virtualenvs")
    session.run(
        "docker",
        "run",
        "--rm",
        "-it" if session.interactive else "-t",
        "-e",
        "CC",
        "-e",
        "USE_COVERAGE",
        "-v",
        f"{os.getcwd()}:/gcovr",
        docker_container_id(session, version),
        *nox_options,
        external=True,
    )


@nox.session(python=False)
def docker(session: nox.Session) -> None:
    """Build and run the docker container for the default GCC version."""
    session_id = f"docker_compiler({GCC_VERSIONS[0]})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_compiler(all)")
def docker_compiler_all(session: nox.Session) -> None:
    """Build and run the docker container for all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_compiler(session: nox.Session, version: str) -> None:
    """Build and run the docker container for a specific GCC version."""
    session_id = "docker_build_compiler({})".format(version)
    session.log(f"Notify session {session_id}")
    session.notify(session_id)
    session_id = f"docker_run_compiler({version})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id, session.posargs)


@nox.session(python=False)
def docker_qa(session: nox.Session) -> None:
    """Run the session qa for the default GCC version."""
    session_id = f"docker_qa_compiler({GCC_VERSIONS[0]})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_qa_compiler(all)")
def docker_qa_compiler_all(session: nox.Session) -> None:
    """Run the session qa for all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_qa_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_compiler(session: nox.Session, version: str) -> None:
    """Run the session qa for a specific GCC version."""
    session_id = f"docker_compiler({version})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id, ["-s", "qa", "--", *session.posargs])
