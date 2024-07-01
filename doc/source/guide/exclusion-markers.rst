.. _exclusion markers:

Exclusion Markers
=================

You can exclude parts of your code from coverage metrics.

-   If ``GCOVR_EXCL_LINE`` appears within a line,
    that line is ignored.
-   If ``GCOVR_EXCL_START`` appears within a line,
    all following lines (including the current line) are ignored
    until a ``GCOVR_EXCL_STOP`` marker is encountered.
-   If ``GCOVR_EXCL_BR_*`` markers are used the same exclusion rules
    apply as above, with the difference being that they are only taken
    into account for branch coverage.

Instead of ``GCOVR_*``,
the markers may also start with ``GCOV_*`` or ``LCOV_*``.
However, start and stop markers must use the same style.
The prefix is configurable with the option
:option:`--exclude-pattern-prefix<gcovr --exclude-pattern-prefix>`.

The excluded region not includes the line with the stop marker::

    code
    code
    excluded       // GCOVR_EXCL_START
    still excluded
    ...
    still excluded
    NOT excluded // GCOVR_EXCL_STOP
    code
    code

In the excluded regions, *any* coverage is excluded.
