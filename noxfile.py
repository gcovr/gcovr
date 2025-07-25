# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
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

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


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
    "clang-17",
    "clang-18",
    "clang-19",
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

    cc_path, cc_file = os.path.split(cc)

    session.env["GCOVR_TEST_SUITE"] = "1"
    session.env["CC"] = os.path.join(cc_path, cc_file)
    session.env["CFLAGS"] = "--this_flag_does_not_exist"
    session.env["CXX"] = os.path.join(
        cc_path, cc_file.replace("clang", "clang++").replace("gcc", "g++")
    )
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
                    .. _next_release:

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


def install_dev_requirements(session: nox.Session, *requirements: str) -> None:
    """Install the needed development packages."""
    with Path("pyproject.toml").open("rb") as fh_in:
        pyproject = tomllib.load(fh_in)
    dev_deps = pyproject["project"]["optional-dependencies"]["dev"]
    session.install(
        *[
            d
            for d in dev_deps
            if any(d.startswith(requirement) for requirement in requirements)
        ]
    )


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
    session.notify("pre-commit")


@nox.session
def ruff_check(session: nox.Session) -> None:
    """Run ruff check command."""
    install_dev_requirements(session, "ruff")
    if session.posargs:
        args = session.posargs
    else:
        args = ["."]
    session.run("ruff", "check", *args)


@nox.session
def ruff_format(session: nox.Session) -> None:
    """Run ruff format command."""
    install_dev_requirements(session, "ruff")
    if session.posargs:
        args = session.posargs
    else:
        args = ["--diff", "."]
    session.run("ruff", "format", *args)


@nox.session
def bandit(session: nox.Session) -> None:
    """Run bandit, a code formatter and format checker."""
    install_dev_requirements(session, "bandit[toml]")
    if session.posargs:
        args = session.posargs
    else:
        args = ["-r", *DEFAULT_LINT_ARGUMENTS]
    session.run("bandit", "-c", "pyproject.toml", *args)


@nox.session
def pylint(session: nox.Session) -> None:
    """Run pylint command."""
    install_dev_requirements(session, "pylint", "nox", "requests", "pytest")
    session.install("-e", ".")
    if session.posargs:
        args = session.posargs
    else:
        args = DEFAULT_LINT_ARGUMENTS
    session.run("pylint", *args)


@nox.session
def mypy(session: nox.Session) -> None:
    """Run mypy command."""
    install_dev_requirements(session, "mypy", "nox", "requests", "pytest", "yaxmldiff")
    session.install("-e", ".")
    if session.posargs:
        args = session.posargs
    else:
        args = ["."]
    session.run("mypy", *args)


@nox.session(name="pre-commit")
def pre_commit(session: nox.Session) -> None:
    """Run pre-commit command."""
    install_dev_requirements(session, "pre-commit")
    if session.posargs:
        args = session.posargs
    else:
        args = ["run", "--all-files"]
    session.run("pre-commit", *args)


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
        with open("examples/gcovr.out", "w", encoding="UTF-8") as fh_out:
            session.run("gcovr", "-h", stdout=fh_out)
        for builder in ("linkcheck", "html", "latex", "epub"):
            if (
                os.environ.get("SPHINX_SKIP_CHECK_LINKS", "") == "True"
                and builder == "linkcheck"
            ):
                session.log(
                    "Skip link checker due to environment SPHINX_SKIP_CHECK_LINKS=True."
                )
                continue
            session.run(
                "sphinx-build",
                "-b",
                builder,
                "-d",
                "build/doctrees",
                "-D",
                "language=en",
                "-W",
                "source",
                f"build/{builder}",
            )
            if builder == "latex" and GCOVR_ISOLATED_TEST:
                with session.chdir("build/latex"):
                    session.run(
                        "latexmk",
                        "-r",
                        "latexmkrc",
                        "-pdf",
                        "-f",
                        "-dvi-",
                        "-ps-",
                        "-jobname=gcovr",
                        "-interaction=nonstopmode",
                        external=True,
                        success_codes=[12],  # To ignore the unicode error
                    )
                    if not Path("gcovr.pdf").exists():
                        session.error("PDF not generated.")

        # Ensure that the README builds fine as a standalone document.
        readme_html = "build/README.html"
        session.run("rst2html5.py", "--strict", "../README.rst", readme_html)

    session.log("Create release_notes.md out of CHANGELOG.rst...")
    changelog_rst = Path("CHANGELOG.rst")
    with changelog_rst.open(encoding="UTF-8") as fh_in:
        lines = fh_in.readlines()

    out_lines = list[str]()
    iter_lines = iter(lines)
    for line in iter_lines:
        if line.startswith("------------"):
            next(iter_lines)
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
        # Remove the empty lines around sub lists
        if (
            line.strip().startswith("- ")
            and out_lines[-1].rstrip() == ""
            and out_lines[-2].startswith("- ")
        ):
            out_lines.pop()
        # Skip lines with link targets
        elif line.startswith(".. ") and line.rstrip().endswith(":"):
            continue
        out_lines.append(line)
    else:
        raise RuntimeError(f"End of release changes not found in {changelog_rst}.")

    release_notes_md = Path() / "doc" / "build" / "release_notes.md"
    with release_notes_md.open("w", encoding="UTF-8") as fh_out:
        fh_out.writelines(out_lines)


@nox.session
def tests(session: nox.Session) -> None:
    """Run the tests with the default GCC version."""
    use_coverage = os.environ.get("USE_COVERAGE") == "true"
    requirements = [
        "cmake",
        "pygments",  # Need a version from dev requirements for reference compare
        "pytest",
        "pytest-timeout",
        "pywin32",
        "yaxmldiff",
    ]
    if use_coverage:
        requirements += ["coverage", "pytest-cov"]
    install_dev_requirements(session, *requirements)
    session.install("-e", ".")
    set_environment(session)
    session.log("Print versions")
    session.run("python", "--version")
    session.run("pip", "freeze")
    # Use full path to executable
    cc = str(session.env["CC"])
    session.env["CC"] = str(shutil.which(cc)).replace(os.path.sep, "/")
    session.run(cc, "--version", external=True)
    cxx = str(session.env["CXX"])
    session.env["CXX"] = str(shutil.which(cxx)).replace(os.path.sep, "/")
    session.run(cxx, "--version", external=True)
    cc_path, cc_file = os.path.split(cc)
    gcov = str(
        shutil.which(
            os.path.join(
                cc_path, cc_file.replace("clang", "llvm-cov").replace("gcc", "gcov")
            )
        )
    ).replace(os.path.sep, "/")
    session.run(gcov, "--version", external=True)
    if "llvm-cov" in gcov:
        gcov += " gcov"
    session.env["GCOV"] = gcov
    session.run("make", "--version", external=True)
    session.run("ninja", "--version", external=True)
    session.log(f"Using reference data for {session.env['CC_REFERENCE']}")

    with session.chdir("tests"):
        session.run("make", "--silent", "clean", external=True)

    args = ["-m", "pytest"]
    if use_coverage:
        args += ["--cov=gcovr", "--cov-branch"]
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


@nox.session(python=False)
def validate_reports(session: nox.Session) -> None:
    """Validate the generated reports where a schema is available."""

    def run_xmllint(file: Path, schema: Path) -> None:
        command = ["xmllint", "--noout"]
        command += (
            ["--nonet", "--dtdvalid"] if schema.suffix == ".dtd" else ["--schema"]
        )
        command += [str(schema), str(file)]
        out = ""
        try:
            out = str(session.run(*command, silent=True, external=True))
        except nox.command.CommandFailed as e:
            session.error(f"{e}\n{out}")

    for test_directory in [Path(p) for p in ("tests", "doc/examples")]:
        cobertura_dtd = Path("tests") / "cobertura.coverage-04.dtd"
        for file in test_directory.rglob("*cobertura*.xml"):
            run_xmllint(file, cobertura_dtd)
        jacoco_dtd = Path("tests") / "JaCoCo.report.dtd"
        for file in test_directory.rglob("*jacoco*.xml"):
            run_xmllint(file, jacoco_dtd)
        clover_schema = Path("tests") / "clover.xsd"
        for file in test_directory.rglob("*clover*.xml"):
            run_xmllint(file, clover_schema)
        sonarqube_schema = Path("tests") / "sonar-generic-coverage.xsd"
        for file in test_directory.rglob("*sonarqube*.xml"):
            run_xmllint(file, sonarqube_schema)


@nox.session
def build_distribution(session: nox.Session) -> None:
    """Build a wheel."""
    install_dev_requirements(session, "build")
    # Remove old dist if present
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    session.run("python", "-m", "build")
    session.notify(("check_distribution"))


@nox.session
def check_distribution(session: nox.Session) -> None:
    """Check the wheel and do a smoke test, should not be used directly."""
    install_dev_requirements(session, "wheel", "twine")
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
    install_dev_requirements(session, "pyinstaller")
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
            # Workaround for "UserWarning: pkg_resources is deprecated as an API"
            "--exclude-module",
            "pkg_resources",
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
                with open(file, encoding="UTF-8") as fh_in:
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
    if session.env["CC"] in [
        "gcc-12",
        "gcc-13",
        "gcc-14",
        "clang-16",
        "clang-17",
        "clang-18",
        "clang-19",
    ]:
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
        "-e",
        "SPHINX_SKIP_CHECK_LINKS",
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
