
.. _markdown_output:

Markdown Output
===============

.. versionadded:: NEXT

The ``gcovr`` command can also generate Markdown output using
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

The :option:`--markdown-theme<gcovr --markdown-theme>` option controls the color theme of the markdown report.

    :option:`--markdown-theme green<gcovr --markdown-theme>`, :option:`--markdown-theme default.green<gcovr --markdown-theme>`

    :option:`--markdown-theme blue<gcovr --markdown-theme>`, :option:`--markdown-theme default.blue<gcovr --markdown-theme>`
