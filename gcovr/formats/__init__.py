import logging
from typing import Callable, List, Optional, Tuple

from ..options import GcovrConfigOption

from ..coverage import CovData

# the handler
from .gcov import handler as gcov_handler
from .cobertura import handler as cobertura_handler
from .html import handler as html_handler
from .json import handler as json_handler
from .txt import handler as txt_handler
from .csv import handler as csv_handler
from .sonarqube import handler as sonarqube_handler
from .coveralls import handler as coveralls_handler

LOGGER = logging.getLogger("gcovr")


def get_options() -> List[GcovrConfigOption]:
    return [
        *gcov_handler.get_options(),
        *txt_handler.get_options(),
        *cobertura_handler.get_options(),
        *html_handler.get_options(),
        *json_handler.get_options(),
        *csv_handler.get_options(),
        *sonarqube_handler.get_options(),
        *coveralls_handler.get_options(),
    ]


def read_reports(covdata: CovData, options) -> bool:
    if json_handler.read_report(covdata, options):
        return True

    if not covdata:
        return gcov_handler.read_report(covdata, options)

    return False


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
                txt_handler.write_report,
                lambda: LOGGER.warning(
                    "Text output skipped - "
                    "consider providing an output file with `--txt=OUTPUT`."
                ),
            )
        )

    if options.cobertura or options.cobertura_pretty:
        generators.append(
            (
                [options.cobertura],
                cobertura_handler.write_report,
                lambda: LOGGER.warning(
                    "Cobertura output skipped - "
                    "consider providing an output file with `--cobertura=OUTPUT`."
                ),
            )
        )

    if options.html or options.html_details or options.html_nested:
        generators.append(
            (
                [options.html, options.html_details, options.html_nested],
                html_handler.write_report,
                lambda: LOGGER.warning(
                    "HTML output skipped - "
                    "consider providing an output file with `--html=OUTPUT`."
                ),
            )
        )

    if options.sonarqube:
        generators.append(
            (
                [options.sonarqube],
                sonarqube_handler.write_report,
                lambda: LOGGER.warning(
                    "Sonarqube output skipped - "
                    "consider providing an output file with `--sonarqube=OUTPUT`."
                ),
            )
        )

    if options.json or options.json_pretty:
        generators.append(
            (
                [options.json],
                json_handler.write_report,
                lambda: LOGGER.warning(
                    "JSON output skipped - "
                    "consider providing an output file with `--json=OUTPUT`."
                ),
            )
        )

    if options.json_summary or options.json_summary_pretty:
        generators.append(
            (
                [options.json_summary],
                json_handler.write_summary_report,
                lambda: LOGGER.warning(
                    "JSON summary output skipped - "
                    "consider providing an output file with `--json-summary=OUTPUT`."
                ),
            )
        )

    if options.csv:
        generators.append(
            (
                [options.csv],
                csv_handler.write_report,
                lambda: LOGGER.warning(
                    "CSV output skipped - "
                    "consider providing an output file with `--csv=OUTPUT`."
                ),
            )
        )

    if options.coveralls or options.coveralls_pretty:
        generators.append(
            (
                [options.coveralls],
                coveralls_handler.write_report,
                lambda: LOGGER.warning(
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
        txt_handler.write_report(
            covdata, "-" if default_output is None else default_output.abspath, options
        )
        default_output = None

    if (
        default_output is not None
        and default_output.value is not None
        and not default_output_used
    ):
        LOGGER.warning(
            f"--output={repr(default_output.value)} option was provided but not used."
        )

    if options.print_summary:
        txt_handler.write_summary_report(covdata, "-", options)

    return generator_error_occurred
