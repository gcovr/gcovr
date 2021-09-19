import os
import shutil
import nox

GCC_VERSIONS = ["gcc-5", "gcc-6", "gcc-8", "clang-10"]
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
    "tests(version='{}')".format(os.environ.get("CC", "gcc-5")),
]


def set_environment(session, cc, check=True):
    if check and (shutil.which(cc) is None):
        session.env["CC_REFERENCE"] = cc
        cc = "gcc"
        cxx = "g++"
        gcov = "gcov"
    else:
        cxx = cc.replace("clang", "clang++").replace("gcc", "g++")
        gcov = cc.replace("clang", "llvm-cov").replace("gcc", "gcov")
    session.env["GCOVR_TEST_SUITE"] = "1"
    session.env["CC"] = cc
    session.env["CFLAGS"] = "--this_flag_does_not_exist"
    session.env["CXX"] = cxx
    session.env["CXXFLAGS"] = "--this_flag_does_not_exist"
    session.env["GCOV"] = gcov


@nox.session
def qa(session):
    for session_id in nox.options.sessions:
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)


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
    set_environment(session, version)
    session.run("bash", "-c", "cd gcovr/tests && make --silent clean", external=True)
    args = ["-m", "pytest"]
    if os.environ.get("USE_COVERAGE") == "true":
        args += ["--cov=gcovr", "--cov-branch"]
    args += session.posargs
    if "--" not in args:
        args += ["--", "gcovr", "doc/examples"]
    session.run("python", *args)


@nox.session
def tests_all_versions(session):
    for version in GCC_VERSIONS:
        session_id = "tests(version='{}')".format(version)
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)


@nox.session
@nox.parametrize("version", GCC_VERSIONS)
def docker_qa(session, version):
    container_id = "gcovr-qa-{}".format(version)
    set_environment(session, version, True)
    session.run(
        "bash",
        "-c",
        " ".join(
            [
                "docker",
                "build",
                "--tag",
                container_id,
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
                "-v",
                "{}:/gcovr".format(os.getcwd()),
                container_id,
            ]
        ),
        external=True,
    )


@nox.session
def docker_qa_all_versions(session):
    for version in GCC_VERSIONS:
        session_id = "docker_qa(version='{}')".format(version)
        session.log("Notify session {}".format(session_id))
        session.notify(session_id)
