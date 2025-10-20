import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.parametrize(
    "metric",
    ["line", "branch", "condition", "decision"],
)
def test_metric(gcovr_test_exec: "GcovrTestExec", metric: str) -> None:
    """Test excluding of functions."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    additional_options = [f"--sonarqube-metric={metric}"]
    if metric == "decision":
        additional_options.append("--decision")
    gcovr_test_exec.gcovr(
        *additional_options,
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()
