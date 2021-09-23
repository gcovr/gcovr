import os
import platform
import shutil
import nox

GCC_VERSIONS = ["gcc-5", "gcc-6", "gcc-8", "clang-10"]
GCC_VERSION2USE = os.environ.get("CC", "gcc-5")
DEFAULT_TEST_DIRECTORIES = ["doc", "gcovr"]
BLACK_CONFORM_FILES = [
    "noxfile.py",
    "gcovr/gcov.py",
    "gcovr/gcov_parser.py",
]

nox.options.sessions = [
    "qa",
    "lint",
    "doc",
    "tests_version({})".format(GCC_VERSION2USE),
]


def set_environment(session: "nox.session", cc: str, check: bool = True) -> None:
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


@nox.session
def qa(session: "nox.session") -> None:
    for session_id in nox.options.sessions:
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)


@nox.session
def lint(session: "nox.session") -> None:
    session.install("flake8")
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
def black(session: "nox.session") -> None:
    session.install("black")
    if session.posargs:
        args = session.posargs
    else:
        raise RuntimeError("Please add the files to format as argument.")
    session.run("python", "-m", "black", *args)


@nox.session
def doc(session: "nox.session") -> None:
    session.install(
        "sphinx",
        "sphinx_rtd_theme",
        "sphinxcontrib-autoprogram==0.1.5 ; python_version=='3.6'",
        "sphinxcontrib-autoprogram>=0.1.5 ; python_version>='3.7'",
    )
    session.install("-e", ".")
    session.run("bash", "-c", "cd doc && make html O=-W", external=True)


@nox.session
def tests(session: "nox.session") -> None:
    session_id = "tests_version({})".format(GCC_VERSION2USE)
    session.log("Notify session {}".format(session_id))
    session.notify(session_id)


@nox.session
def tests_all_versions(session: "nox.session") -> None:
    for version in GCC_VERSIONS:
        session_id = "tests_version({})".format(version)
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)


@nox.session
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def tests_version(session: "nox.session", version: str) -> None:
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
    session.run(
        session.env["GCOV"].replace(" gcov", "")
        if "llvm-cov" in session.env["GCOV"]
        else session.env["GCOV"],
        "--version",
        external=True,
    )

    session.run("bash", "-c", "cd gcovr/tests && make --silent clean", external=True)
    args = ["-m", "pytest"]
    args += coverage_args
    args += session.posargs
    if "--" not in args:
        args += ["--", "gcovr", "doc/examples"]
    session.run("python", *args)


@nox.session
def build_wheel(session: "nox.session") -> None:
    session.install("wheel", "twine")
    session.run("python", "setup.py", "sdist", "bdist_wheel")
    session.run("twine", "check", "dist/*", external=True)


@nox.session
def upload_wheel(session: "nox.session") -> None:
    session.install("twine")
    session.run("twine", "upload", "dist/*", external=True)


def docker_container_id(version: str) -> None:
    return "gcovr-qa-{}".format(version)


@nox.session
def docker_qa_build(session: "nox.session") -> None:
    session_id = "docker_qa__build_version({})".format(GCC_VERSION2USE)
    session.log("Notify session {}".format(session_id))
    session.notify(session_id)


@nox.session
def docker_qa_build_all_versions(session: "nox.session") -> None:
    for version in GCC_VERSIONS:
        session_id = "docker_qa_build_version({})".format(version)
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)


@nox.session
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_build_version(session: "nox.session", version: str) -> None:
    set_environment(session, version, False)
    session.run(
        "bash",
        "-c",
        " ".join(
            [
                "docker",
                "build",
                "--tag",
                docker_container_id(version),
                "--build-arg",
                "USERID={}".format(os.geteuid()),
                "--build-arg",
                "CC=${CC}",
                "--build-arg",
                "CXX=${CXX}",
                "--file",
                "admin/Dockerfile.qa",
                ".",
            ]
        ),
        external=True,
    )


@nox.session
def docker_qa_run(session: "nox.session") -> None:
    session_id = "docker_qa_run_version({})".format(GCC_VERSION2USE)
    session.log("Notify session {}".format(session_id))
    session.notify(session_id)


@nox.session
def docker_qa_run_all_versions(session: "nox.session") -> None:
    for version in GCC_VERSIONS:
        session_id = "docker_qa_run_version({})".format(version)
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)


@nox.session
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_run_version(session: "nox.session", version: str) -> None:
    set_environment(session, version, False)
    session.run(
        "bash",
        "-c",
        " ".join(
            [
                "docker",
                "run",
                "--rm",
                "-e",
                "TESTOPTS",
                "-e",
                "CC",
                "-v",
                "{}:/gcovr".format(os.getcwd()),
                docker_container_id(version),
            ]
        ),
        external=True,
    )


@nox.session
def docker_qa(session: "nox.session") -> None:
    session_id = "docker_qa_build_version({})".format(GCC_VERSION2USE)
    session.log("Notify session {}".format(session_id))
    session.notify(session_id)
    session_id = "docker_qa_run_version({})".format(GCC_VERSION2USE)
    session.log("Notify session {}".format(session_id))
    session.notify(session_id)


@nox.session
def docker_qa_all_versions(session: "nox.session") -> None:
    for version in GCC_VERSIONS:
        session_id = "docker_qa_build_version({})".format(version)
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)
        session_id = "docker_qa_run_version({})".format(version)
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)


@nox.session
@nox.parametrize("version", [nox.param(v, id=v) for v in GCC_VERSIONS])
def docker_qa_version(session: "nox.session", version: str) -> None:
    session_id = "docker_qa_build_version({})".format(version)
    session.log("Notify session {}".format(session_id))
    session.notify(session_id)
    session_id = "docker_qa_run_version({})".format(version)
    session.log("Notify session {}".format(session_id))
    session.notify(session_id)
