from pathlib import Path
import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_absolute(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test for filtering source files using absolute filepaths from existing unfiltered JSON report."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
        gcovr_test_exec.cxx_compile("file1.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        f"--filter={(gcovr_test_exec.output_dir / 'main.cpp').as_posix()}",
        "--json-pretty",
        "--json=coverage.json",
    )

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


def test_absolute_from_unfiltered_tracefile(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test for filtering source files using absolute filepaths from existing unfiltered JSON report."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
        gcovr_test_exec.cxx_compile("file1.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--json-pretty", "--json", "coverage_unfiltered.json")

    filter_option = f"--filter={(gcovr_test_exec.output_dir / 'main.cpp').as_posix()}"

    gcovr_test_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        filter_option,
        "--json-add-tracefile=coverage_unfiltered.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


def test_relative(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test for filtering source files using relative filepaths."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
        gcovr_test_exec.cxx_compile("file1.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--filter=main.cpp",
        "--json-pretty",
        "--json=coverage.json",
    )

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


def test_relative_from_unfiltered_tracefile(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test for filtering source files using relative filepaths from existing unfiltered JSON report."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
        gcovr_test_exec.cxx_compile("file1.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--json-pretty", "--json", "coverage_unfiltered.json")

    gcovr_test_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--lcov=coverage.lcov",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--filter=main.cpp",
        "--json-add-tracefile=coverage_unfiltered.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


def test_relative_lib(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test for filtering source files using relative filepaths."""
    for entry in (gcovr_test_exec.output_dir / "relative_lib").glob("*"):
        entry.rename(gcovr_test_exec.output_dir / entry.name)
    (gcovr_test_exec.output_dir / "project" / "relevant-library").symlink_to(
        Path("..", "external-library"),
        target_is_directory=True,
    )
    gcovr_test_exec.run("sh", "-c", "ls -alR project project/relevant-library")
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile(
            "src/main.cpp",
            target="main.o",
            cwd=Path("project"),
        ),
        gcovr_test_exec.cxx_compile(
            "ignore-this/no.cpp",
            target="no.o",
            cwd=Path("project"),
        ),
        gcovr_test_exec.cxx_compile(
            "relevant-library/src/yes.cpp",
            target="yes.o",
            cwd=Path("project"),
        ),
        cwd=Path("project"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("project"))
    prefix = r"\.\." if gcovr_test_exec.is_windows() else ".*"
    gcovr_test_exec.gcovr(
        f"--filter={prefix}/external-library/src",
        "--json-pretty",
        "--json=../coverage.json",
        cwd=Path("project"),
    )

    gcovr_test_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--html-details",
        "--html=../coverage.html",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--txt=../coverage.txt",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--cobertura-pretty",
        "--cobertura=../cobertura.xml",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--coveralls-pretty",
        "--coveralls=../coveralls.json",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--jacoco=../jacoco.xml",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--lcov=../coverage.lcov",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--config=src/gcovr_add_tracefile.cfg",
        "--sonarqube=../sonarqube.xml",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_sonarqube()


def test_relative_lib_from_unfiltered_tracefile(
    gcovr_test_exec: "GcovrTestExec",
) -> None:
    """A simple test for filtering source files using relative filepaths."""
    for entry in (gcovr_test_exec.output_dir / "relative_lib").glob("*"):
        entry.rename(gcovr_test_exec.output_dir / entry.name)
    (gcovr_test_exec.output_dir / "project" / "relevant-library").symlink_to(
        Path("..", "external-library"),
        target_is_directory=True,
    )
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile(
            "src/main.cpp",
            target="main.o",
            cwd=Path("project"),
        ),
        gcovr_test_exec.cxx_compile(
            "ignore-this/no.cpp",
            target="no.o",
            cwd=Path("project"),
        ),
        gcovr_test_exec.cxx_compile(
            "relevant-library/src/yes.cpp",
            target="yes.o",
            cwd=Path("project"),
        ),
        cwd=Path("project"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("project"))
    gcovr_test_exec.gcovr(
        "--config=gcovr_empty.cfg",
        "--json-pretty",
        "--json=../coverage.json",
        cwd=Path("project"),
    )

    gcovr_test_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--txt=../coverage.txt",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--jacoco=../jacoco.xml",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--lcov=../coverage.lcov",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--cobertura-pretty",
        "--cobertura=../cobertura.xml",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--filter=../external-library/src",
        "--config=src/gcovr_add_tracefile.cfg",
        "--sonarqube=../sonarqube.xml",
        cwd=Path("project"),
    )
    gcovr_test_exec.compare_sonarqube()
