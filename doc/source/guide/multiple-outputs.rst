.. _multiple output formats:

Multiple Output Formats
=======================

You can write multiple report formats with one gcovr invocation
by passing the output filename directly to the report format flag.
If no filename is specified for the format,
the value from :option:`-o/--output<gcovr --output>` is used by default,
which itself defaults to stdout.

The following report format flags can take an optional output file name:

- :option:`gcovr --csv`
- :option:`gcovr --txt`
- :option:`gcovr --cobertura`
- :option:`gcovr --html`
- :option:`gcovr --html-details`
- :option:`gcovr --html-nested`
- :option:`gcovr --sonarqube`
- :option:`gcovr --json`
- :option:`gcovr --json-summary`
- :option:`gcovr --coveralls`

If the value given to the output option ends with a path seperator (``/`` or ``\``)
it is used a directory which is created first and a default filename depending
on the format is used.

Note that :option:`--html-details<gcovr --html-details>` and
:option:`--html-nested<gcovr --html-nested>` override any value of
:option:`--html<gcovr --html>` if it is present.
