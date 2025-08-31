.. program:: gcovr

.. _markdown_output:

Markdown Output
===============

.. versionadded:: NEXT

The ``gcovr`` command can generate Markdown output using
the :option:`--markdown` option::

    gcovr --markdown coverage.md

If you just need a summary of the coverage information, you can use
:option:`--markdown-summary` instead (see :ref:`markdown_summary_output`).

If the given name ends with the suffix ``.gz`` the report is compressed by gzip.

.. _markdown_summary_output:

Markdown Summary Output
-----------------------

The :option:`--markdown-summary` option outputs coverage summary,
without file information.

The :option:`--markdown-theme` option controls the color theme of the markdown report.

    :option:`--markdown-theme green <--markdown-theme>`, :option:`--markdown-theme default.green <--markdown-theme>`

    :option:`--markdown-theme blue <--markdown-theme>`, :option:`--markdown-theme default.blue <--markdown-theme>`
