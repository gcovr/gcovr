.. _exclusion markers:

Exclusion Markers
=================

You can exclude parts of your code from coverage metrics.

-   If ``GCOVR_EXCL_LINE`` appears within a line,
    that line is ignored.
-   If ``GCOVR_EXCL_START`` appears within a line,
    all following lines (including the current line) are ignored
    until a ``GCOVR_EXCL_STOP`` marker is encountered.

Instead of ``GCOVR_*``,
the markers may also start with ``GCOV_*`` or ``LCOV_*``.
However, start and stop markers must use the same style.
The prefix is configurable with the option
:option:`--exclude-pattern-prefix<gcovr --exclude-pattern-prefix>`.

In the excluded regions, *any* coverage is excluded.
It is not currently possible to exclude only branch coverage in that region.
In particular, lcov's EXCL_BR markers are not supported
(see issue :issue:`121`).
