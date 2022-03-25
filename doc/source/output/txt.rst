.. _text_output:
.. _txt_output:

Text Output
===========

The text output format summarizes coverage in a plain-text table.
This is the default output format if no other format is selected.
This output format can also be explicitly selected
with the :option:`gcovr --txt` option.

.. versionadded:: 5.0
   Added explicit :option:`--txt<gcovr --txt>` option.

Example output:

.. include:: ../../examples/example.txt
    :literal:

Line Coverage
-------------

Running gcovr without any explicit output formats …

.. include:: ../../examples/example.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

generates a text summary of the lines executed:

.. include:: ../../examples/example.txt
    :literal:

The same result can be achieved when explicit :option:`--txt<gcovr --txt>`
option is set. For example::

    gcovr --txt

generates the same text summary.

Each line of this output includes a summary for a given source file,
including the number of lines instrumented, the number of lines
executed, the percentage of lines executed, and a summary of the
line numbers that were not executed.  To improve clarity, gcovr
uses an aggressive approach to grouping uncovered lines and will
combine uncovered lines separated by "non-code" lines (blank,
freestanding braces, and single-line comments) into a single region.
As a result, the number of lines listed in the "Missing" list may
be greater than the difference of the "Lines" and "Exec" columns.

Note that ``gcov`` accumulates statistics by line.  Consequently, it
works best with a programming style that places only one statement
on each line.

..
    In ``example.cpp``, the ``MACRO`` macro executes a
    branch, but ``gcov`` cannot discern which branch is executed.


Branch Coverage
---------------

The ``gcovr`` command can also summarize branch coverage using
the :option:`-b/--branches<gcovr --branches>` option:

.. include:: ../../examples/example_branches.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates a tabular output that summarizes the number of branches, the number of
branches taken and the branches that were not completely covered:

.. include:: ../../examples/example_branches.txt
    :literal:

The same result can be achieved when explicit :option:`--txt<gcovr --txt>`
option is set. For example::

    gcovr --branches --txt

prints the same tabular output.
