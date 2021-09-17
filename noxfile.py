import os
import sys
import nox
from nox import sessions
from nox.sessions import Session

GCC_VERSIONS = ["gcc-5", "gcc-6", "gcc-8", "clang-10", "all"]
DEFAULT_TEST_DIRECTORIES = ["doc", "gcovr"]
BLACK_CONFORM_FILES = [
    "noxfile.py",
    "gcovr/gcov.py",
    "gcovr/gcov_parser.py",
]

nox.options.sessions = ["lint", "doc", "tests(version='gcc-5')"]


@nox.session
def lint(session):
    session.install("flake8", "black")
    if session.posargs:
        args = session.posargs
    else:
        args = DEFAULT_TEST_DIRECTORIES
    session.run("flake8", *args)
    
    if session.posargs:
        session.run("python", "-m", "black", *session.posargs)
    else:
        session.run(
            "python", "-m", "black", "--diff", "--check", *BLACK_CONFORM_FILES
        )
        session.run("python", "-m", "black", "--diff", *DEFAULT_TEST_DIRECTORIES)


@nox.session
def black(session):
    session.install("black")
    if session.posargs:
        args = session.posargs
    else:
        args = "."
    session.run("python", "-m", "black", *args)


@nox.session
def black(session):
    session.install("black")


@nox.session
def doc(session):
    session.install("-r", "requirements.txt")
    session.install("-r", "doc/requirements.txt")
    session.install("-e", ".")
    session.run("bash", "-c", "cd doc && make html O=-W", external=True)


@nox.session
@nox.parametrize("version", GCC_VERSIONS)
def tests(session, version):
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    if version == "all":
        for version in GCC_VERSIONS:
            if not version == "all":
                tests(session, version)
    else:
        if os.environ.get("USE_COVERAGE") == "true":
            args = ["--cov=gcovr", "--cov-branch"].append(args)

        session.env["GCOVR_TEST_SUITE"] = "1"
        session.env["CC"] = version
        session.env["CFLAGS"] = "--this_flag_does_not_exist"
        session.env["CXX"] = version.replace("clang", "clang++").replace("gcc", "g++")
        session.env["CXXFLAGS"] = "--this_flag_does_not_exist"
        session.env["GCOV"] = version.replace("clang", "llvm-cov").replace(
            "gcc", "gcov"
        )
        session.run(
            "bash", "-c", "cd gcovr/tests && make --silent clean", external=True
        )
        args = ["-m", "pytest"]
        args += session.posargs
        if "--" not in args:
            args += ["--", "gcovr", "doc/examples"]
        session.run("python", *args)
