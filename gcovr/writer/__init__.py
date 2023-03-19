
import logging
from typing import Callable, List, Optional, Tuple

from ..coverage import CovData

# the writers
from .cobertura import print_cobertura_report
from .html import print_html_report
from .json import print_json_report, print_json_summary_report
from .txt import print_text_report
from .csv import print_csv_report
from .summary import print_summary
from .sonarqube import print_sonarqube_report
from .coveralls import print_coveralls_report

logger = logging.getLogger("gcovr")


def write_reports(covdata: CovData, options):
    from ..configuration import Options, OutputOrDefault

    Generator = Tuple[
        List[Optional[OutputOrDefault]],
        Callable[[CovData, str, Options], None],
        Callable[[], None],
    ]
    generators: List[Generator] = []

    if options.txt:
        generators.append(
            (
                [options.txt],
                print_text_report,
                lambda: logger.warning(
                    "Text output skipped - "
                    "consider providing an output file with `--txt=OUTPUT`."
                ),
            )
        )

    if options.cobertura or options.cobertura_pretty:
        generators.append(
            (
                [options.cobertura],
                print_cobertura_report,
                lambda: logger.warning(
                    "Cobertura output skipped - "
                    "consider providing an output file with `--cobertura=OUTPUT`."
                ),
            )
        )

    if options.html or options.html_details or options.html_nested:
        generators.append(
            (
                [options.html, options.html_details, options.html_nested],
                print_html_report,
                lambda: logger.warning(
                    "HTML output skipped - "
                    "consider providing an output file with `--html=OUTPUT`."
                ),
            )
        )

    if options.sonarqube:
        generators.append(
            (
                [options.sonarqube],
                print_sonarqube_report,
                lambda: logger.warning(
                    "Sonarqube output skipped - "
                    "consider providing an output file with `--sonarqube=OUTPUT`."
                ),
            )
        )

    if options.json or options.json_pretty:
        generators.append(
            (
                [options.json],
                print_json_report,
                lambda: logger.warning(
                    "JSON output skipped - "
                    "consider providing an output file with `--json=OUTPUT`."
                ),
            )
        )

    if options.json_summary or options.json_summary_pretty:
        generators.append(
            (
                [options.json_summary],
                print_json_summary_report,
                lambda: logger.warning(
                    "JSON summary output skipped - "
                    "consider providing an output file with `--json-summary=OUTPUT`."
                ),
            )
        )

    if options.csv:
        generators.append(
            (
                [options.csv],
                print_csv_report,
                lambda: logger.warning(
                    "CSV output skipped - "
                    "consider providing an output file with `--csv=OUTPUT`."
                ),
            )
        )

    if options.coveralls or options.coveralls_pretty:
        generators.append(
            (
                [options.coveralls],
                print_coveralls_report,
                lambda: logger.warning(
                    "Coveralls output skipped - "
                    "consider providing an output file with `--coveralls=OUTPUT`."
                ),
            )
        )

    generator_error_occurred = False
    reports_were_written = False
    default_output_used = False
    default_output = OutputOrDefault(None) if options.output is None else options.output

    for output_choices, generator, on_no_output in generators:
        output = OutputOrDefault.choose(output_choices, default=default_output)
        if output is not None and output is default_output:
            default_output_used = True
            if not output.is_dir:
                default_output = None
        if output is not None:
            if generator(covdata, output.abspath, options):
                generator_error_occurred = True
            reports_were_written = True
        else:
            on_no_output()

    if not reports_were_written:
        print_text_report(
            covdata, "-" if default_output is None else default_output.abspath, options
        )
        default_output = None

    if (
        default_output is not None
        and default_output.value is not None
        and not default_output_used
    ):
        logger.warning(
            f"--output={repr(default_output.value)} option was provided but not used."
        )

    if options.print_summary:
        print_summary(covdata, options)

    return generator_error_occurred
