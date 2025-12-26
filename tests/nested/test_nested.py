from pathlib import Path
import re
import shutil
from sys import stderr
from unittest import mock

import pytest

from tests.conftest import GCOVR_ISOLATED_TEST, USE_PROFDATA_POSSIBLE, GcovrTestExec


def test_standard(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test nested coverage report generation."""
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
    )

    gcovr_test_exec.run("./subdir/testcase")
    gcovr_test_exec.gcovr("--root=subdir", "--json-pretty", "--json=coverage.json")
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--root=subdir", "--json-add-tracefile=coverage.json", "--txt", "coverage.txt"
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--markdown",
        "coverage.md",
        "--markdown-summary",
        "coverage_summary.md",
        "--markdown-file-link",
        "http://link/to/file/{file}",
    )
    gcovr_test_exec.compare_markdown()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--lcov=coverage.lcov",
        "--lcov-format-1.x",
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--clover-pretty",
        "--clover=clover.xml",
        "--clover-project",
        "Test project",
    )
    gcovr_test_exec.compare_clover()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--jacoco-pretty",
        "--jacoco=jacoco.xml",
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()


@pytest.mark.skipif(
    not GCOVR_ISOLATED_TEST,
    reason="Only available in isolated docker test.",
)
def test_standard_ccache(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test nested coverage report generation."""
    build_dir = gcovr_test_exec.output_dir / "build"
    for run in range(2):
        print(f"***** Build with ccache ({run}) *****", file=stderr)
        with mock.patch.dict(
            "os.environ",
            {"CCACHE_DIR": str(gcovr_test_exec.output_dir / "ccache")},
        ):
            if build_dir.exists():
                shutil.rmtree(build_dir)
            build_dir.mkdir()
            gcovr_test_exec.cxx_link(
                "subdir/testcase",
                *[
                    gcovr_test_exec.cxx_compile(
                        source,
                        target=str(build_dir / (Path(source).name + ".o")),
                        launcher="ccache",
                    )
                    for source in [
                        "subdir/A/file1.cpp",
                        "subdir/A/File2.cpp",
                        "subdir/A/file3.cpp",
                        "subdir/A/File4.cpp",
                        "subdir/A/file7.cpp",
                        "subdir/A/C/file5.cpp",
                        "subdir/A/C/D/File6.cpp",
                        "subdir/B/main.cpp",
                    ]
                ],
                launcher="ccache",
            )
            process = gcovr_test_exec.run("ccache", "--show-stats", cwd=build_dir)
            rate = 0 if run == 0 else 100
            check.is_true(
                re.search(
                    rf"(?:cache hit rate\s+{rate}.00 %|Hits:.+\(\s*{rate}.0{'' if rate else '0'}\s*%\))",
                    process.stdout,
                )
            )
            gcovr_test_exec.run("ccache", "--zero-stats", cwd=build_dir)

            gcovr_test_exec.run("./subdir/testcase")
            gcovr_test_exec.gcovr(
                "--root=subdir",
                "--json-pretty",
                f"--json=coverage{'' if run == 0 else '.cached'}.json",
                str(build_dir),
            )
    gcovr_test_exec.compare_json()
    gcovr_test_exec.run("diff", "-U", "1", "coverage.json", "coverage.cached.json")


@pytest.mark.skipif(
    not USE_PROFDATA_POSSIBLE,
    reason="LLVM profdata is not compatible with GCC coverage data.",
)
def test_standard_llvm_profdata(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test nested coverage report generation."""
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("subdir"))
    gcovr_test_exec.gcovr(
        "--llvm-cov-binary=./testcase",
        "--trace-include=.+/file.\\.cpp$",
        "--json-pretty",
        "--json=../coverage.json",
        cwd=Path("subdir"),
    )
    gcovr_test_exec.compare_json()


def test_threaded(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test nested coverage report generation."""
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
    )

    gcovr_test_exec.run(
        "./testcase",
        cwd=Path("subdir"),
    )
    gcovr_test_exec.gcovr(
        "-j=-1",
        "--json-pretty",
        "--json=../coverage.json",
        cwd=Path("subdir"),
    )
    gcovr_test_exec.compare_json()


def test_linked(gcovr_test_exec: "GcovrTestExec") -> None:
    """This test case was inspired by the logic in gcovr
    that traverses symbolic links:

    UNIX resolves symbolic links by walking the
    entire directory structure.  What that means is that relative links
    are always relative to the actual directory inode, and not the
    "virtual" path that the user might have traversed (over symlinks) on
    the way to that directory.  Here's the canonical example:

      a / b / c / testfile
      a / d / e --> ../../a/b
      m / n --> /a
      x / y / z --> /m/n/d

    If we start in "y", we will see the following directory structure:
      y
      |-- z
          |-- e
              |-- c
                  |-- testfile


    """
    source_root = gcovr_test_exec.output_dir / "subdir"
    target_root = gcovr_test_exec.output_dir / "nested" / "subdir"
    target_root.parent.mkdir()
    source_root.rename(target_root)
    source_root.mkdir()
    (source_root / "B").symlink_to(target_root / "B")
    (source_root / "m").mkdir()
    (source_root / "m" / "n").symlink_to(target_root / "A")
    (source_root / "A").symlink_to(source_root / "m" / "n")
    (source_root / "loop").symlink_to(source_root)
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
    )

    gcovr_test_exec.run("./subdir/testcase")
    gcovr_test_exec.gcovr("--json-pretty", "--json=coverage.json")
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--html-theme=github.green",
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr("--json-add-tracefile=coverage.json", "--txt", "coverage.txt")
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
        "--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--lcov", "coverage.lcov"
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube", "sonarqube.xml"
    )
    gcovr_test_exec.compare_sonarqube()


def test_use_existing(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test nested2-use-existing coverage."""
    # Build all required binaries
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
    )
    gcovr_test_exec.run("./subdir/testcase")
    # Simulate gcov and subdir/A coverage if needed
    gcovr_test_exec.gcovr(
        "--root=subdir",
        "-g",
        "-k",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()


def test_oos(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test nested with oos build."""
    (gcovr_test_exec.output_dir / "objs").mkdir()
    cwd = gcovr_test_exec.output_dir / "subdir"
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("A/file1.cpp", target="../objs/file1.o", cwd=cwd),
        gcovr_test_exec.cxx_compile("A/File2.cpp", target="../objs/file2.o", cwd=cwd),
        gcovr_test_exec.cxx_compile("A/file3.cpp", target="../objs/file3.o", cwd=cwd),
        gcovr_test_exec.cxx_compile("A/File4.cpp", target="../objs/file4.o", cwd=cwd),
        gcovr_test_exec.cxx_compile("A/file7.cpp", target="../objs/file7.o", cwd=cwd),
        gcovr_test_exec.cxx_compile("A/C/file5.cpp", target="../objs/file5.o", cwd=cwd),
        gcovr_test_exec.cxx_compile(
            "A/C/D/File6.cpp", target="../objs/file6.o", cwd=cwd
        ),
        gcovr_test_exec.cxx_compile("B/main.cpp", target="../objs/main.o", cwd=cwd),
        cwd=cwd,
    )

    gcovr_test_exec.run("./subdir/testcase")
    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--gcov-object-directory=objs",
        "--exclude-function-lines",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--html-details",
        "--no-html-details-syntax-highlighting",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--root=subdir", "--json-add-tracefile=coverage.json", "--txt", "coverage.txt"
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--cobertura-pretty",
        "--cobertura=cobertura.xml",
    )
    gcovr_test_exec.compare_cobertura()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()

    gcovr_test_exec.gcovr(
        "--root=subdir", "--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--root=subdir", "--json-add-tracefile=coverage.json", "--lcov", "coverage.lcov"
    )
    gcovr_test_exec.compare_lcov()

    gcovr_test_exec.gcovr(
        "--root=subdir",
        "--json-add-tracefile=coverage.json",
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()
