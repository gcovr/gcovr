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

from .conftest import GCOVR_ISOLATED_TEST, IS_GCC, GcovrTestExec


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
    name = shell_script.name.split(".", maxsplit=1)[0]
    output_format = name.split("_", maxsplit=1)[1] if "_" in name else "txt"
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

    scrub_function = getattr(
        gcovr_test_exec._compare, f"scrub_{output_format}", lambda x: x
    )

    # Read old file
    baseline = baseline_file.read_bytes().decode(encoding="UTF-8")
    baseline_scrubbed = scrub_function(baseline)
    try:
        gcovr_test_exec.run("sh", "-c", shell_script, cwd=EXAMPLES_DIRECTORY)
        # Read new data
        current = baseline_file.read_bytes().decode(encoding="UTF-8")
        current_scrubbed = scrub_function(current)

        gcovr_test_exec._compare.assert_equals(
            baseline_file,
            baseline_scrubbed,
            Path("<STDOUT>"),
            current_scrubbed,
            encoding="utf8",
        )
    finally:
        if not gcovr_test_exec._compare.update_reference:
            baseline_file.write_text(baseline, encoding="UTF-8")


def test_timestamps_example(gcovr_test_exec: "GcovrTestExec") -> None:
    """Run the timestamp example."""
    gcovr_test_exec.run("sh", "example_timestamps.sh", cwd=EXAMPLES_DIRECTORY)
