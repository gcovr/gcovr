# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.4+main, a parsing and reporting tool for gcov.
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

from pathlib import Path
import pytest

from tests.conftest import GCOVR_ISOLATED_TEST, IS_GCC, GcovrTestExec


EXAMPLES_DIRECTORY = Path(__file__).parent.parent / "doc" / "examples"
SHELL_SCRIPTS = [
    p for p in EXAMPLES_DIRECTORY.glob("*.sh") if "timestamp" not in p.name
]


@pytest.mark.skipif(
    not (GCOVR_ISOLATED_TEST and IS_GCC),
    reason="Only available for GCC in isolated docker test.",
)
@pytest.mark.parametrize("shell_script", SHELL_SCRIPTS, ids=lambda p: p.stem)
def test_examples(gcovr_test_exec: "GcovrTestExec", shell_script: Path) -> None:
    """Run the examples as tests."""
    gcovr_test_exec.copy_source(EXAMPLES_DIRECTORY / "example.cpp")
    gcovr_test_exec.copy_source(shell_script)
    if "cmake" in shell_script.name:
        gcovr_test_exec.copy_source(EXAMPLES_DIRECTORY / "CMakeLists.txt")
    name = shell_script.name.split(".", maxsplit=1)[0]
    output_format = name.split("_", maxsplit=1)[1]
    if output_format in ("branches", "cmake"):
        output_format = "txt"
    elif output_format == "json_summary":
        output_format = "json"
    if (
        output_format in ("html", "cobertura")
        and gcovr_test_exec.is_gcc()
        and (gcovr_test_exec.cc_version() in [5, 6, 14])
    ):
        gcovr_test_exec.skip(
            f"GCC {gcovr_test_exec.cc_version()} have broken HTML output."
        )

    if (
        output_format == "json"
        and gcovr_test_exec.is_gcc()
        and gcovr_test_exec.cc_version() == 14
    ):
        gcovr_test_exec.skip(
            f"GCC {gcovr_test_exec.cc_version()} has broken JSON output."
        )

    extension = (
        "xml" if output_format in ("cobertura", "clover", "jacoco") else output_format
    )
    baseline_file = EXAMPLES_DIRECTORY / f"{name}.{extension}"
    output_file = gcovr_test_exec.output_dir / baseline_file.name

    scrub_function = getattr(
        gcovr_test_exec._compare,  # pylint: disable=protected-access
        f"scrub_{output_format}",
        lambda x: x,
    )

    # Read old file
    baseline = baseline_file.read_bytes().decode(encoding="UTF-8")
    baseline_scrubbed = scrub_function(baseline)
    current = None
    try:
        gcovr_test_exec.run(
            "sh",
            "-c",
            gcovr_test_exec.output_dir / shell_script.name,
        )
        # Read new data
        current = output_file.read_bytes().decode(encoding="UTF-8")
        current_scrubbed = scrub_function(current)

        gcovr_test_exec._compare.assert_equals(  # pylint: disable=protected-access
            baseline_file,
            baseline_scrubbed,
            output_file,
            current_scrubbed,
            encoding="utf8",
        )
    finally:
        if current is not None and gcovr_test_exec._compare.update_reference:  # pylint: disable=protected-access
            if output_format == "html":
                for file in [
                    gcovr_test_exec.output_dir / "example_html.html",
                    *gcovr_test_exec.output_dir.glob("example_html.details.*"),
                ]:
                    file.rename(EXAMPLES_DIRECTORY / file.name)
            else:
                output_file.rename(baseline_file)


def test_timestamps_example(gcovr_test_exec: "GcovrTestExec") -> None:
    """Run the timestamp example."""
    gcovr_test_exec.run("sh", "example_timestamps.sh", cwd=EXAMPLES_DIRECTORY)
