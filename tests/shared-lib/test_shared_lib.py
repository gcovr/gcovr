import os
import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    # Build shared library and test app

    (gcovr_test_exec.output_dir / "obj").mkdir()
    (gcovr_test_exec.output_dir / "testApp" / "test").mkdir()
    if gcovr_test_exec.is_windows():
        shared_lib_extension = ".dll"
        shared_lib_flags = ["-shared"]
    elif gcovr_test_exec.is_darwin():
        shared_lib_extension = ".dylib"
        shared_lib_flags = ["-dynamiclib", "-undefined", "dynamic_lookup"]
    else:
        shared_lib_extension = ".so"
        shared_lib_flags = ["-shared"]

    run_env = os.environ.copy()
    if gcovr_test_exec.is_windows():
        run_env.update(
            {
                "PATH": os.pathsep.join(
                    [
                        f"{gcovr_test_exec.output_dir}/lib",
                        os.environ.get("PATH", ""),
                    ]
                )
            }
        )
    else:
        run_env.update(
            {
                "LD_LIBRARY_PATH": f"{gcovr_test_exec.output_dir}/lib",
            }
        )

    gcovr_test_exec.cxx_link(
        f"lib/libs{shared_lib_extension}",
        *shared_lib_flags,
        gcovr_test_exec.cxx_compile("lib/lib.cpp", target="obj/lib.o"),
    )
    gcovr_test_exec.cxx(
        "-I../lib",
        "tmp.cpp",
        "-o",
        "test/a.out",
        "-L../lib",
        "-ls",
        cwd=gcovr_test_exec.output_dir / "testApp",
    )

    # Run test app and generate coverage.json
    gcovr_test_exec.run("sh", "-c", "testApp/test/a.out", env=run_env)
    gcovr_test_exec.gcovr("--json-pretty", "--json=coverage.json")

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
        "--html-details",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--sonarqube", "sonarqube.xml"
    )
    gcovr_test_exec.compare_sonarqube()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json", "--jacoco", "jacoco.xml"
    )
    gcovr_test_exec.compare_jacoco()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
    )
    gcovr_test_exec.compare_coveralls()
