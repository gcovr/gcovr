# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2024 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from contextlib import ExitStack
import functools
import io
import os
from pathlib import Path
import platform
import re
from runpy import run_path
import socket
import sys
import textwrap
import time
from typing import Optional
import shutil
import subprocess  # nosec # Commands are trusted.
import zipfile

import nox

import requests


GCOVR_ISOLATED_TEST = os.getenv("GCOVR_ISOLATED_TEST") == "zkQEVaBpXF1i"
ALL_COMPILER_VERSIONS = [
    "gcc-5",
    "gcc-6",
    "gcc-8",
    "gcc-9",
    "gcc-10",
    "gcc-11",
    "gcc-12",
    "gcc-13",
    "gcc-14",
    "clang-10",
    "clang-13",
    "clang-14",
    "clang-15",
    "clang-16",
]
DEFAULT_COMPILER_VERSION = ALL_COMPILER_VERSIONS[0]

ALL_COMPILER_VERSIONS_NEWEST_FIRST = [
    "-".join(cc)
    for cc in sorted(
        [(*cc.split("-"),) for cc in ALL_COMPILER_VERSIONS],
        key=lambda cc: (cc[0], int(cc[1])),
        reverse=True,
    )
]

ALL_GCC_VERSIONS = [v for v in ALL_COMPILER_VERSIONS if v.startswith("gcc-")]
ALL_CLANG_VERSIONS = [v for v in ALL_COMPILER_VERSIONS if v.startswith("clang-")]

DEFAULT_TEST_DIRECTORIES = ["doc", "src", "tests"]
DEFAULT_LINT_ARGUMENTS = [
    "noxfile.py",
    "scripts",
    "admin",
] + DEFAULT_TEST_DIRECTORIES

OUTPUT_FORMATS = [
    "cobertura",
    "coveralls",
    "csv",
    "html-details",
    "json",
    "sonarqube",
    "txt",
]

CI_RUN = "GITHUB_ACTION" in os.environ
GCOVR_CHANGELOG_RST = Path(__file__).parent / "CHANGELOG.rst"

nox.options.sessions = ["qa"]


def get_gcovr_version() -> str:
    """Get the current GCOVR version without the date."""
    return re.sub(
        r"\.d\d+$",
        "",
        run_path(str(Path(__file__).parent / "src" / "gcovr" / "version.py"))[
            "__version__"
        ],
    )


def get_gcc_versions() -> tuple[str, str]:
    """Get the gcc version from the environment or from the output of the executable."""
    # If the user explicitly set CC variable, use that directly without checks.
    cc = os.environ.get("CC")
    if cc is None:
        # Find the first installed compiler version we support
        for command in ALL_COMPILER_VERSIONS_NEWEST_FIRST:
            if shutil.which(command):
                return (command, command)
    elif cc_reference := os.environ.get("CC_REFERENCE"):
        return (cc, cc_reference)

    commands = ["gcc", "clang"] if cc is None else [cc]

    for command in commands:
        if shutil.which(command):
            output = subprocess.check_output([command, "--version"]).decode()  # nosec # The command is not a user input

            # cspell:ignore Linaro xctoolchain
            # look for a line "gcc WHATEVER VERSION.WHATEVER" in output like:
            #   gcc-5 (Ubuntu/Linaro 5.5.0-12ubuntu1) 5.5.0 20171010
            #   Copyright (C) 2015 Free Software Foundation, Inc.
            #   This is free software; see the source for copying conditions.  There is NO
            #   warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
            search_gcc_version = re.search(r"^gcc\b.* ([0-9]+)\..+$", output, re.M)

            # look for a line "WHATEVER clang version VERSION.WHATEVER" in output like:
            #    Apple clang version 13.1.6 (clang-1316.0.21.2.5)
            #    Target: arm64-apple-darwin21.5.0
            #    Thread model: posix
            #    InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
            search_clang_version = re.search(
                r"\bclang version ([0-9]+)\.", output, re.M
            )

            if search_gcc_version:
                major_version = search_gcc_version.group(1)
                return (command, f"gcc-{major_version}")

            if search_clang_version:
                major_version = search_clang_version.group(1)
                return (command, f"clang-{major_version}")

    raise RuntimeError(
        "Could not detect a valid compiler, you can define one by setting the environment CC"
    )


def set_environment(session: nox.Session, cc: Optional[str] = None) -> None:
    """Set the environment variables"""
    if cc is None:
        cc, cc_reference = get_gcc_versions()
    else:
        cc_reference = cc
    session.env["GCOVR_TEST_SUITE"] = "1"
    session.env["CC"] = cc
    session.env["CFLAGS"] = "--this_flag_does_not_exist"
    session.env["CXX"] = cc.replace("clang", "clang++").replace("gcc", "g++")
    session.env["CXXFLAGS"] = "--this_flag_does_not_exist"
    if cc_reference is not None:
        session.env["CC_REFERENCE"] = cc_reference


@nox.session()
def prepare_release(session: nox.Session) -> None:
    """Prepare the release"""
    session.install("-e", ".")
    version = get_gcovr_version()
    parts = version.split(".", maxsplit=2)
    if len(parts) == 2:
        session.error("Session only allowed for development iteration")
    major, minor = parts[0:2]
    session.log("Is this a major release (1) or a minor release (2)?")
    release_type = input()
    if release_type == "1":
        major = str(int(major) + 1)
        minor = "0"
    elif release_type == "2":
        # hatchling has already set the correct version
        pass
    else:
        session.error(f"Invalid input {release_type!r}")

    session.run("python", "admin/bump_version.py", f"{major}.{minor}")
    html2jpeg(session)


@nox.session()
def prepare_next_iteration(session: nox.Session) -> None:
    """Prepare the next iteration"""
    session.install("-e", ".")
    new_lines = []
    lines = iter(GCOVR_CHANGELOG_RST.read_text().splitlines())
    for line in lines:
        if re.match(r"^\d+\.\d+ \(", line):
            new_lines.append(
                textwrap.dedent(
                    """\
                    Next Release
                    ------------

                    Known bugs:

                    Breaking changes:

                    New features and notable changes:

                    Bug fixes and small improvements:

                    Documentation:

                    Internal changes:
                    """
                )
            )
            last_version = line.split(" ", maxsplit=1)[0]
            new_lines.append(line)
            break
        if line == "Next Release":
            session.error("Next release can only be prepared after a released version")
        new_lines.append(line)
    else:
        session.error(f"Version line not found in {GCOVR_CHANGELOG_RST.name}")
    new_lines += list(lines)

    GCOVR_CHANGELOG_RST.write_text("\n".join(new_lines))

    session.run("python", "admin/bump_version.py", f"{last_version}+main")
    session.notify("html2jpeg")


@nox.session(python=False)
def qa(session: nox.Session) -> None:
    """Run the quality tests for the default GCC version."""
    for session_id in ["lint", "doc", "tests"]:
        session.log(f"Notify session {session_id}")
        session.notify(session_id, [])


@nox.session(python=False)
def lint(session: nox.Session) -> None:
    """Run the linters."""
    session.notify("ruff_check")
    session.notify("ruff_format")
    session.notify("bandit")
    session.notify("pylint")
    session.notify("mypy")


@nox.session
def ruff_check(session: nox.Session) -> None:
    """Run ruff check command."""
    session.install("ruff~=0.7.0")
    if session.posargs:
        args = session.posargs
    else:
        args = DEFAULT_LINT_ARGUMENTS
    session.run("ruff", "check", *args)


@nox.session
def ruff_format(session: nox.Session) -> None:
    """Run ruff format command."""
    session.install("ruff~=0.7.0")
    if session.posargs:
        args = session.posargs
    else:
        args = ["--diff", *DEFAULT_LINT_ARGUMENTS]
    session.run("ruff", "format", *args)


@nox.session
def bandit(session: nox.Session) -> None:
    """Run bandit, a code formatter and format checker."""
    session.install("bandit[toml]")
    if session.posargs:
        args = session.posargs
    else:
        args = ["-r", *DEFAULT_LINT_ARGUMENTS]
    session.run("bandit", "-c", "pyproject.toml", *args)


@nox.session
def pylint(session: nox.Session) -> None:
    """Run pylint command."""
    session.install("pylint<4.0.0", "nox", "requests", "pytest")
    if sys.version_info >= (3, 12):
        session.install("setuptools")
    session.install("-e", ".")
    if session.posargs:
        args = session.posargs
    else:
        args = DEFAULT_LINT_ARGUMENTS
    session.run("pylint", *args)


@nox.session
def mypy(session: nox.Session) -> None:
    """Run mypy command."""
    session.install("mypy", "nox", "requests", "pytest", "yaxmldiff")
    session.install("-e", ".")
    if session.posargs:
        args = session.posargs
    else:
        args = ["--install-types", "--non-interactive", *DEFAULT_LINT_ARGUMENTS]
    session.run("mypy", *args)


@nox.session
def doc(session: nox.Session) -> None:
    """Generate the documentation."""
    session.install("-r", "doc/requirements.txt", "docutils")
    session.install("-e", ".")

    if not GCOVR_ISOLATED_TEST and not (
        # Github actions on MacOs can't use Docker
        platform.system() == "Darwin" and CI_RUN
    ):
        docker_build_compiler(session, "gcc-8")
        # We need to inject the arguments
        session._runner.posargs = ["-s", "tests", "--", "-k", "test_example"]  # pylint: disable=protected-access
        docker_run_compiler(session, "gcc-8")

    # Build the Sphinx documentation
    with session.chdir("doc"):
        with open("examples/gcovr.out", "w", encoding="utf-8") as fh_out:
            session.run("gcovr", "-h", stdout=fh_out)
        session.run("sphinx-build", "-M", "html", "source", "build", "-W")

    # Ensure that the README builds fine as a standalone document.
    readme_html = session.create_tmp() + "/README.html"
    session.run("rst2html5.py", "--strict", "README.rst", readme_html)

    session.log("Create release_notes.md out of CHANGELOG.rst...")
    changelog_rst = Path("CHANGELOG.rst")
    with changelog_rst.open(encoding="utf-8") as fh_in:
        lines = fh_in.readlines()

    out_lines = list[str]()
    iter_lines = iter(lines)
    for line in iter_lines:
        if line.startswith("------------"):
            next(iter_lines)
            version = get_gcovr_version()
            out_lines += [
                f"{version}\n",
                f"{'-' * len(version)}\n",
                "\n",
            ]
            break
        if (line.rstrip())[:-1] == ":":
            raise RuntimeError(f"Found section start before release ID: {line}")
    else:
        raise RuntimeError(f"Start of release changes not found in {changelog_rst}.")

    for line in iter_lines:
        if re.fullmatch(r"\d+\.\d+\s+\(.+\)", line.rstrip()):
            break
        line, _ = re.subn(r"``", r"`", line)
        line, _ = re.subn(r":(?:option|ref):", r"", line)
        line, _ = re.subn(r":issue:`(\d+)`", r"#\1", line)
        if line.strip().startswith("- ") and out_lines[-1].rstrip() == "":
            out_lines.pop()
        out_lines.append(line)
    else:
        raise RuntimeError(f"End of release changes not found in {changelog_rst}.")

    release_notes_md = Path() / "doc" / "build" / "release_notes.md"
    with release_notes_md.open("w", encoding="utf-8") as fh_out:
        fh_out.writelines(out_lines)


@nox.session
def tests(session: nox.Session) -> None:
    """Run the tests with the default GCC version."""
    session.install(
        "jinja2",
        "lxml",
        "pygments==2.13.0",
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
    set_environment(session)
    session.log("Print tool versions")
    session.run("python", "--version")
    # Use full path to executable
    session.env["CC"] = str(shutil.which(session.env["CC"])).replace(os.path.sep, "/")
    session.run(session.env["CC"], "--version", external=True)
    session.env["CXX"] = str(shutil.which(session.env["CXX"])).replace(os.path.sep, "/")
    session.run(session.env["CXX"], "--version", external=True)
    session.env["GCOV"] = str(
        shutil.which(
            session.env["CC"].replace("clang", "llvm-cov").replace("gcc", "gcov")
        )
    ).replace(os.path.sep, "/")

    session.run(session.env["GCOV"], "--version", external=True)
    if "llvm-cov" in session.env["GCOV"]:
        session.env["GCOV"] += " gcov"
    session.log(f"Using reference data for {session.env['CC_REFERENCE']}")

    with session.chdir("tests"):
        session.run("make", "--silent", "clean", external=True)

    args = ["-m", "pytest"]
    args += coverage_args
    args += session.posargs
    if "--" not in args:
        args += ["--"] + DEFAULT_TEST_DIRECTORIES

    # Delay the session failure,
    # even if command fail we want to get the coverage report.
    try:
        session.run(
            "python",
            *args,
        )
    finally:
        if os.environ.get("USE_COVERAGE") == "true":
            session.run("coverage", "xml")
            if not CI_RUN:
                session.run("coverage", "html")


@nox.session
def build_wheel(session: nox.Session) -> None:
    """Build a wheel."""
    session.install("build")
    # Remove old dist if present
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    session.run("python", "-m", "build")
    session.notify(("check_wheel"))


@nox.session
def check_wheel(session: nox.Session) -> None:
    """Check the wheel and do a smoke test, should not be used directly."""
    session.install("wheel", "twine")
    with session.chdir("dist"):
        session.run("twine", "check", "*", external=True)
        session.run("pip", "uninstall", "--yes", "gcovr")
        session.install(str(list(Path().glob("*.whl"))[0]))
    session.run("python", "-m", "gcovr", "--help", external=True)
    session.run("gcovr", "--help", external=True)
    session.log("Run all transformations to check if all the modules are packed")
    with session.chdir(session.create_tmp()):
        for output_format in OUTPUT_FORMATS:
            session.run(
                "gcovr", f"--{output_format}", f"out.{output_format}", external=True
            )


@nox.session
def upload_wheel(session: nox.Session) -> None:
    """Upload the wheel."""
    session.install("twine")
    session.run("twine", "upload", "dist/*", external=True)


@functools.lru_cache(maxsize=1)
def get_executable_name() -> Path:
    """Get the executable name."""
    if platform.system() == "Windows":
        suffix = ".exe"
    else:
        suffix = ""
    if platform.system() == "Windows":
        platform_suffix = "win"
    elif platform.system() == "Darwin":
        platform_suffix = "macos"
    else:
        platform_suffix = "linux"
    return Path(
        f"gcovr-{get_gcovr_version()}-{platform_suffix}-{platform.machine().lower()}{suffix}"
    )


@nox.session
def bundle_app(session: nox.Session) -> None:
    """Bundle a standalone executable."""
    session.install("pyinstaller~=6.11.1")
    # This is needed if the virtual env is reused
    session.run("pip", "uninstall", "gcovr")
    # Do not install interactive to get the module resolved
    # with the needed data
    session.install(".")
    os.makedirs("build", exist_ok=True)
    with session.chdir("build"):
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
            "gcovr",
            "-n",
            str(get_executable_name()),
            *session.posargs,
            "../scripts/pyinstaller_entrypoint.py",
        )
        session.notify("check_bundled_app")


@nox.session(python=False)
def check_bundled_app(session: nox.Session) -> None:
    """Run a smoke test with the bundled app, should not be used directly."""
    with session.chdir("build"):
        executable = get_executable_name().absolute()
        session.run(str(executable), "--help", external=True)
        session.log("Run all transformations to check if all the modules are packed")
        with session.chdir(session.create_tmp()):
            for output_format in OUTPUT_FORMATS:
                session.run(
                    str(executable),
                    f"--{output_format}",
                    f"out.{output_format}",
                    external=True,
                )


@nox.session()
def html2jpeg(session: nox.Session) -> None:
    """Create JPEGs from HTML for documentation"""
    session.install("requests")

    # Create a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to localhost and let the OS assign a free port number
    sock.bind(("localhost", 0))
    # Get the assigned port number
    port = sock.getsockname()[1]
    # Close the socket
    sock.close()

    with ExitStack() as defer:
        container_id = subprocess.check_output(  # nosec # We run on several system and do not know the full path
            [
                "docker",
                "run",
                "--rm",
                "--detach",
                "-p",
                f"{port}:2305",
                "bedrockio/export-html",
            ]
        ).strip()

        def docker_stop() -> None:
            subprocess.run(["docker", "stop", container_id], check=False)  # nosec # We run on several system and do not know the full path

        defer.callback(docker_stop)
        url = f"http://localhost:{port}/1/screenshot"
        time.sleep(5.0)  # nosemgrep # We need to wait here until server is started.

        def screenshot(html: str, jpeg: str, size: tuple[int, int]) -> None:
            def read_file(file: str) -> str:
                with open(file, encoding="utf-8") as fh_in:
                    return " ".join(fh_in.readlines()).replace("\n", "")

            content = re.sub(
                r'<link rel="stylesheet" href="([^"]+)"/>',
                lambda match: f'<style type="text/css">{read_file(os.path.join(os.path.dirname(html), match[1]))}</style>',
                read_file(html),
            )
            payload = {
                "html": content,
                "export": {
                    "type": "jpeg",
                    "fullPage": False,
                    "clip": {"x": 1, "y": 1, "width": size[0], "height": size[1]},
                },
            }
            session.log(f"Generating {jpeg} from {html}...")
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            with open(jpeg, mode="bw") as fh_out:
                fh_out.write(response.content)

        screenshot(
            "doc/examples/example_html.html",
            "doc/images/screenshot-html.jpeg",
            (800, 290),
        )
        screenshot(
            "doc/examples/example_html.details.example.cpp.9597a7a3397b8e3a48116e2a3afb4154.html",
            "doc/images/screenshot-html-details.example.cpp.jpeg",
            (800, 600),
        )
        screenshot(
            "tests/html-themes/reference/gcc-5/coverage.green.main.cpp.118fcbaaba162ba17933c7893247df3a.html",
            "doc/images/screenshot-html-default-green-src.jpeg",
            (800, 290),
        )
        screenshot(
            "tests/html-themes/reference/gcc-5/coverage.blue.main.cpp.118fcbaaba162ba17933c7893247df3a.html",
            "doc/images/screenshot-html-default-blue-src.jpeg",
            (800, 290),
        )
        screenshot(
            "tests/html-themes-github/reference/gcc-5/coverage.green.main.cpp.118fcbaaba162ba17933c7893247df3a.html",
            "doc/images/screenshot-html-github-green-src.jpeg",
            (800, 500),
        )
        screenshot(
            "tests/html-themes-github/reference/gcc-5/coverage.blue.main.cpp.118fcbaaba162ba17933c7893247df3a.html",
            "doc/images/screenshot-html-github-blue-src.jpeg",
            (800, 500),
        )
        screenshot(
            "tests/html-themes-github/reference/gcc-5/coverage.dark-green.main.cpp.118fcbaaba162ba17933c7893247df3a.html",
            "doc/images/screenshot-html-github-dark-green-src.jpeg",
            (800, 500),
        )
        screenshot(
            "tests/html-themes-github/reference/gcc-5/coverage.dark-blue.main.cpp.118fcbaaba162ba17933c7893247df3a.html",
            "doc/images/screenshot-html-github-dark-blue-src.jpeg",
            (800, 500),
        )


def docker_container_os(session: nox.Session) -> str:
    """Get the version of the OS for the used GCC version."""
    if session.env["CC"] in ["gcc-5", "gcc-6"]:
        return "ubuntu:18.04"
    if session.env["CC"] in ["gcc-8", "gcc-9", "clang-10"]:
        return "ubuntu:20.04"
    if session.env["CC"] in ["gcc-10", "gcc-11", "clang-13", "clang-14", "clang-15"]:
        return "ubuntu:22.04"
    if session.env["CC"] in ["gcc-12", "gcc-13", "gcc-14", "clang-16"]:
        return "ubuntu:24.04"

    raise RuntimeError(f"No container image defined for {session.env['CC']}")


def docker_container_id(session: nox.Session, version: str) -> str:
    """Get the docker container ID."""
    return f"gcovr-{docker_container_os(session).replace(':', '_')}-{version}-uid_{os.geteuid()}"


@nox.session(python=False)
def docker_build(session: nox.Session) -> None:
    """Build the docker container for the default GCC version."""
    session_id = f"docker_build({DEFAULT_COMPILER_VERSION})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_build_compiler(all)")
def docker_build_compiler_all(session: nox.Session) -> None:
    """Build the docker containers vor all compiler versions."""
    for version in ALL_COMPILER_VERSIONS:
        session_id = f"docker_build_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False, name="docker_build_compiler(gcc)")
def docker_build_compiler_gcc(session: nox.Session) -> None:
    """Build the docker containers vor all GCC versions."""
    for version in ALL_GCC_VERSIONS:
        session_id = f"docker_build_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False, name="docker_build_compiler(clang)")
def docker_build_compiler_clang(session: nox.Session) -> None:
    """Build the docker containers vor all CLANG versions."""
    for version in ALL_CLANG_VERSIONS:
        session_id = f"docker_build_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in ALL_COMPILER_VERSIONS])
def docker_build_compiler(session: nox.Session, version: str) -> None:
    """Build the docker container for a specific GCC version."""
    set_environment(session, version)
    container_id = docker_container_id(session, version)
    cache_options = []
    if CI_RUN:
        session.log(
            "Create a builder because the default on doesn't support the gha cache"
        )
        session.run(
            "docker",
            "buildx",
            "create",
            "--name",
            "gha-container",
            "--driver=docker-container",
            "--driver-opt=default-load=true",
            external=True,
        )
        cache_options += [
            "--builder=gha-container",
            "--cache-to",
            f"type=gha,mode=max,scope={container_id}",
            "--cache-from",
            f"type=gha,scope={container_id}",
        ]
    session.run(
        "docker",
        "build",
        *cache_options,
        "--tag",
        container_id,
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
    session_id = f"docker_run_compiler({DEFAULT_COMPILER_VERSION})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_run_compiler(all)")
def docker_run_compiler_all(session: nox.Session) -> None:
    """Run the docker container for the all compiler versions."""
    for version in ALL_COMPILER_VERSIONS:
        session_id = f"docker_run_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False, name="docker_run_compiler(gcc)")
def docker_run_compiler_gcc(session: nox.Session) -> None:
    """Run the docker containers vor all GCC versions."""
    for version in ALL_GCC_VERSIONS:
        session_id = f"docker_run_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False, name="docker_run_compiler(clang)")
def docker_run_compiler_clang(session: nox.Session) -> None:
    """Run the docker containers vor all CLANG versions."""
    for version in ALL_CLANG_VERSIONS:
        session_id = f"docker_run_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in ALL_COMPILER_VERSIONS])
def docker_run_compiler(session: nox.Session, version: str) -> None:
    """Run the docker container for a specific GCC version."""
    set_environment(session, version)

    nox_options = session.posargs if session.posargs else ["-s", "qa"]
    if not session.interactive:
        nox_options.insert(0, "--non-interactive")
    if session._runner.global_config.no_install:  # pylint: disable=protected-access
        nox_options.insert(0, "--no-install")
    if session._runner.global_config.reuse_existing_virtualenvs:  # pylint: disable=protected-access
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
        "-e",
        "FORCE_COLOR",
        "-e",
        f"HOST_OS={platform.system()}",
        "-v",
        f"{os.getcwd()}:/gcovr",
        docker_container_id(session, version),
        *nox_options,
        external=True,
    )


@nox.session(python=False)
def docker(session: nox.Session) -> None:
    """Build and run the docker container for the default GCC version."""
    session_id = f"docker_compiler({DEFAULT_COMPILER_VERSION})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False, name="docker_compiler(all)")
def docker_compiler_all(session: nox.Session) -> None:
    """Build and run the docker container for all compiler versions."""
    for version in ALL_COMPILER_VERSIONS:
        session_id = f"docker_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False, name="docker_compiler(gcc)")
def docker_compiler_gcc(session: nox.Session) -> None:
    """Build and run the docker containers vor all GCC versions."""
    for version in ALL_GCC_VERSIONS:
        session_id = f"docker_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False, name="docker_compiler(clang)")
def docker_compiler_clang(session: nox.Session) -> None:
    """Build and run the docker containers vor all CLANG versions."""
    for version in ALL_CLANG_VERSIONS:
        session_id = f"docker_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in ALL_COMPILER_VERSIONS])
def docker_compiler(session: nox.Session, version: str) -> None:
    """Build and run the docker container for a specific GCC version."""
    session_id = f"docker_build_compiler({version})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)
    session_id = f"docker_run_compiler({version})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id, session.posargs)


@nox.session(python=False)
def import_reference(session: nox.Session) -> None:
    """Import reference data from ZIP generated in Github pipeline."""
    if len(session.posargs) < 1:
        session.error(
            "Please provide the ZIP files to import. Usage: nox -s import_reference -- file.zip"
        )

    def extract(fh_zip: zipfile.ZipFile) -> None:
        for entry in fh_zip.filelist:
            session.log(fh_zip.extract(entry, "tests"))

    for file in session.posargs:
        with zipfile.ZipFile(file) as fh_zip:
            try:
                zip_info_diff_zip = fh_zip.getinfo("diff.zip")
                with fh_zip.open(zip_info_diff_zip) as fh_inner_zip:
                    seekable_buf = io.BytesIO(fh_inner_zip.read())
                    with zipfile.ZipFile(seekable_buf) as fh_diff_zip:
                        extract(fh_diff_zip)
            except KeyError:
                extract(fh_zip)
