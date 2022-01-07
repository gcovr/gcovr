import glob
import os
import platform
import shutil
import shlex
import sys
import nox

GCC_VERSIONS = ["gcc-5", "gcc-6", "gcc-8", "clang-10"]
GCC_VERSION2USE = os.path.split(os.environ.get("CC", "gcc-5"))[1]
DEFAULT_TEST_DIRECTORIES = ["doc", "gcovr"]
BLACK_CONFORM_FILES = [
    "noxfile.py",
    "gcovr/gcov.py",
    "gcovr/gcov_parser.py",
    "gcovr/timestamps.py",
    "gcovr/writer/json.py",
]

nox.options.sessions = ["qa"]
nox.options.reuse_existing_virtualenvs = True

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
def lint(session: nox.Session) -> None:
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
            session.run(
                "python", "-m", "black", "--diff", "--check", *BLACK_CONFORM_FILES
            )
        session.run("python", "-m", "black", "--diff", *args)
    else:
        session.log(
            f"Skip black because of platform {platform.python_implementation()}."
        )


@nox.session
def black(session: nox.Session) -> None:
    """Run black, a code formatter and format checker."""
    session.install("black")
    if session.posargs:
        session.run("python", "-m", "black", *session.posargs)
    else:
        session.run(
            "python", "-m", "black", "--diff", "--check", *BLACK_CONFORM_FILES
        )
        session.run("python", "-m", "black", "--diff", *DEFAULT_TEST_DIRECTORIES)


@nox.session
def doc(session: nox.Session) -> None:
    """Generate the documentation."""
    session.install("-r", "doc/requirements.txt")
    session.install("-e", ".")
    session.chdir("doc")
    session.run("make", "html", "O=-W", external=True)


@nox.session(python=False)
def tests(session: nox.Session) -> None:
    """Run the tests with the default GCC version."""
    session_id = f"tests_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
def tests_all_compiler(session: nox.Session) -> None:
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
        args += ["--", "gcovr", "doc/examples"]
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


@nox.session(reuse_venv=False)
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


def docker_container_id(version: str) -> str:
    """Get the docker container ID."""
    return f"gcovr-qa-{version}-uid_{os.geteuid()}"


@nox.session(python=False)
def docker_qa_build(session: nox.Session) -> None:
    """Build the docker container for the default GCC version."""
    session_id = f"docker_qa_build_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
def docker_qa_build_all_compiler(session: nox.Session) -> None:
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
def docker_qa_run(session: nox.Session) -> None:
    """Run the docker container for the default GCC version."""
    session_id = f"docker_qa_run_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
def docker_qa_run_all_compiler(session: nox.Session) -> None:
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
    if sys.version_info >= (3, 8):
        session.env["NOX_POSARGS"] = shlex.join(session.posargs)
    else:
        # Code for join taken from Python 3.9
        session.env["NOX_POSARGS"] = ' '.join(shlex.quote(arg) for arg in session.posargs)
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
def docker_qa(session: nox.Session) -> None:
    """Build and run the docker container for the default GCC version."""
    session_id = f"docker_qa_compiler({GCC_VERSION2USE})"
    session.log(f"Notify session {session_id}")
    session.notify(session_id)


@nox.session(python=False)
def docker_qa_all_compiler(session: nox.Session) -> None:
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
