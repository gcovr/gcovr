import logging
from typing import Any, Callable, List, Optional, Tuple

from ..options import GcovrConfigOption, Options

from ..coverage import CovData
from ..formats.base import handler_base

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
        Callable[[CovData, str, Options], bool],
        Callable[[], None],
    ]
    generators: List[Generator] = []

    def get_format_data(format_handler: handler_base, summary: bool = False) -> Tuple[Generator, Options]:
        format_writer = (
            format_handler.write_summary_report if summary else format_handler.write_report
        )
        global_options = [
            "timestamp",
            "root",
            "root_dir",
            "root_filter",
            "show_branch",
            "exclude_calls",
            "show_decision",
            "sort_uncovered",
            "sort_percent",
            "search_path",
            "source_encoding",
            "starting_dir",
            "filter",
            "exclude",
        ]
        option_dict = {}
        for name in global_options + [o.name for o in format_handler.get_options()]:
            option_dict[name] = options.get(name)
        return (format_writer, Options(**option_dict))

    if options.txt:
        generators.append(
            (
                [options.txt],
                *get_format_data(txt_handler),
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
                *get_format_data(cobertura_handler),
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
                *get_format_data(html_handler),
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
                *get_format_data(sonarqube_handler),
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
                *get_format_data(json_handler),
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
                *get_format_data(json_handler, summary=True),
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
                *get_format_data(csv_handler),
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
                *get_format_data(coveralls_handler),
                lambda: LOGGER.warning(
                    "Coveralls output skipped - "
                    "consider providing an output file with `--coveralls=OUTPUT`."
                ),
            )
        )

    writer_error_occurred = False
    reports_were_written = False
    default_output_used = False
    default_output = OutputOrDefault(None) if options.output is None else options.output

    for output_choices, format_writer, format_options, on_no_output in generators:
        output = OutputOrDefault.choose(output_choices, default=default_output)
        if output is not None and output is default_output:
            default_output_used = True
            if not output.is_dir:
                default_output = None
        if output is not None:
            if format_writer(covdata, output.abspath, format_options):
                writer_error_occurred = True
            reports_were_written = True
        else:
            on_no_output()

    if not reports_were_written:
        format_writer, format_options = get_format_data(txt_handler)
        format_writer(
            covdata, "-" if default_output is None else default_output.abspath, format_options
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

    if options.txt_summary:
        format_writer, format_options = get_format_data(txt_handler, summary=True)
        format_writer(covdata, "-", format_options)

    return writer_error_occurred
