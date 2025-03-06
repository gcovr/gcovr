
.. _markdown_output:

Markdown Output
===============

.. versionadded:: 9.0

The ``gcovr`` command can lso generate Markdown output using
the :option:`--markdown<gcovr --markdown>` option::

    gcovr --markdown coverage.md

If you just need a summary of the coverage information,
you can use :option:`--markdown-summary<gcovr --markdown-summary>`
instead (see :ref:`markdown_summary_output`).

.. _markdown_summary_output:

Markdown Summary Output
-----------------------

The :option:`--markdown-summary<gcovr --markdown-summary>` option outputs coverage summary,
without file information.
