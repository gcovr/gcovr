import os
import platform
import shutil
import shlex
import nox

GCC_VERSIONS = ["gcc-5", "gcc-6", "gcc-8", "clang-10"]
GCC_VERSION2USE = os.environ.get("CC", "gcc-5")
DEFAULT_TEST_DIRECTORIES = ["doc", "gcovr"]
BLACK_CONFORM_FILES = [
    "noxfile.py",
    "gcovr/gcov.py",
    "gcovr/gcov_parser.py",
]


nox.options.sessions = ["qa"]


def set_environment(session: nox.session, cc: str, check: bool = True) -> None:
    if check and (shutil.which(cc) is None):
        session.env["CC_REFERENCE"] = cc
        cc = "gcc"
        cxx = "g++"
        gcov = "gcov"
    else:
        cxx = cc.replace("clang", "clang++").replace("gcc", "g++")
        if cc.startswith("clang"):
            gcov = cc.replace("clang", "llvm-cov") + " gcov"
        else:
            gcov = cc.replace("gcc", "gcov")
    session.env["GCOVR_TEST_SUITE"] = "1"
    session.env["CC"] = cc
    session.env["CFLAGS"] = "--this_flag_does_not_exist"
    session.env["CXX"] = cxx
    session.env["CXXFLAGS"] = "--this_flag_does_not_exist"
    session.env["GCOV"] = gcov


@nox.session(python=False)
def qa(session: nox.session) -> None:
    """Run the quality tests."""
    session_id = "lint"
    session.log(f"Notify session {session_id}")
    session.notify(session_id, [])
    session_id = "doc"
    session.log(f"Notify session {session_id}")
    session.notify(session_id, [])
    session_id = f"tests_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session
def lint(session: nox.session) -> None:
    """Run the lint (flake8 and black)."""
    session.install("flake8")
    # Black installs under Pypy but doesn't necessarily run (cf psf/black#2559).
    if platform.python_implementation() == "CPython":
        session.install("black")
    if session.posargs:
        args = session.posargs
    else:
        args = DEFAULT_TEST_DIRECTORIES
    session.run("flake8", *args)

    if platform.python_implementation() == "CPython":
        if session.posargs:
            session.run("python", "-m", "black", *session.posargs)
        else:
            session.run(
                "python", "-m", "black", "--diff", "--check", *BLACK_CONFORM_FILES
            )
            session.run("python", "-m", "black", "--diff", *DEFAULT_TEST_DIRECTORIES)
    else:
        session.log(
            f"Skip black because of platform {platform.python_implementation()}."
        )


@nox.session
def black(session: nox.session) -> None:
    """Run black, a code formatter and format checker."""
    session.install("black")
    if session.posargs:
        args = session.posargs
    else:
        raise RuntimeError("Please add the files to format as argument.")
    session.run("python", "-m", "black", *args)


@nox.session
def doc(session: nox.session) -> None:
    """Generate the documentation."""
    session.install("-r", "doc/requirements.txt")
    session.install("-e", ".")
    session.chdir("doc")
    session.run("make", "html", "O=-W", external=True)


@nox.session(python=False)
def tests(session: nox.session) -> None:
    """Run the tests with the default GCC version."""
    session_id = f"tests_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
def tests_all_compiler(session: nox.session) -> None:
    """Run the tests with all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"tests_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def tests_compiler(session: nox.session, version: str) -> None:
    """Run the test with a specifiv GCC version."""
    session.install(
        "jinja2",
        "lxml",
        "pygments==2.7.4",
        "pytest",
        "cmake",
        "yaxmldiff",
    )
    coverage_args = []
    if os.environ.get("USE_COVERAGE") == "true":
        session.install("pytest-cov")
        coverage_args = ["--cov=gcovr", "--cov-branch"]
    session.install("-e", ".")
    set_environment(session, version)
    session.log("Print tool versions")
    session.run("python", "--version")
    session.run(session.env["CC"], "--version", external=True)
    session.run(session.env["CXX"], "--version", external=True)
    session.run(*shlex.split(session.env["GCOV"]), "--version", external=True)

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
        args += ["--", "gcovr", "doc/examples"]
    session.run("python", *args)


@nox.session
def build_wheel(session: nox.session) -> None:
    """Build a wheel."""
    session.install("wheel", "twine")
    session.run("python", "setup.py", "sdist", "bdist_wheel")
    session.run("twine", "check", "dist/*", external=True)


@nox.session
def upload_wheel(session: nox.session) -> None:
    """Upload the wheel."""
    session.install("twine")
    session.run("twine", "upload", "dist/*", external=True)


def docker_container_id(version: str) -> str:
    """Get the docker container ID."""
    return f"gcovr-qa-{version}-uid_{os.geteuid()}"


@nox.session(python=False)
def docker_qa_build(session: nox.session) -> None:
    """Build the docker container for the default GCC version."""
    session_id = f"docker_qa_build_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
def docker_qa_build_all_compiler(session: nox.session) -> None:
    """Build the docker containers vor all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_qa_build_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_build_compiler(session: nox.session, version: str) -> None:
    """Build the docker container for a specific GCC version."""
    set_environment(session, version, False)
    session.run(
        "docker",
        "build",
        "--tag",
        docker_container_id(version),
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
def docker_qa_run(session: nox.session) -> None:
    """Run the docker container for the default GCC version."""
    session_id = f"docker_qa_run_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
def docker_qa_run_all_compiler(session: nox.session) -> None:
    """Run the docker container for the all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_qa_run_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_run_compiler(session: nox.session, version: str) -> None:
    """Run the docker container for a specific GCC version."""
    set_environment(session, version, False)
    session.env["NOX_POSARGS"] = " ".join([repr(a) for a in session.posargs])
    session.run(
        "docker",
        "run",
        "--rm",
        "-e",
        "CC",
        "-e",
        "NOX_POSARGS",
        "-v",
        f"{os.getcwd()}:/gcovr",
        docker_container_id(version),
        external=True,
    )


@nox.session(python=False)
def docker_qa(session: nox.session) -> None:
    """Build and run the docker container for the default GCC version."""
    session_id = f"docker_qa_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
def docker_qa_all_compiler(session: nox.session) -> None:
    """Build and run the docker container for the all GCC versions."""
    for version in GCC_VERSIONS:
        session_id = f"docker_qa_compiler({version})"
        session.log(f"Notify session {session_id}")
        session.notify(session_id)


@nox.session(python=False)
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_compiler(session: nox.session, version: str) -> None:
    """Build and run the docker container for a specific GCC version."""
    session_id = "docker_qa_build_compiler({})".format(version)
    session.log(f"Notify session {session_id}")
    session.notify(session_id)
    session_id = f"docker_qa_run_compiler({version})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)
