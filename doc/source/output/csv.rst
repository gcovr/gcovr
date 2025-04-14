.. program:: gcovr

.. _csv_output:

CSV Output
==========

The :option:`--csv` option output comma-separated values
summarizing the coverage of each file. Consider the following command:

.. literalinclude:: ../../examples/example_csv.sh
    :language: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an CSV:

.. literalinclude:: ../../examples/example_csv.csv
    :language: text

Be careful if you print the output of a CSV to STDOUT and redirect it to
a file. According to :rfc:`4180`, the line endings must be CRLF.

.. versionadded:: 5.0
   Added :option:`--csv`.
