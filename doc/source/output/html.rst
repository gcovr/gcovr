.. _html_output:

HTML Output
===========

The ``gcovr`` command can also generate a simple
HTML output using the :option:`--html<gcovr --html>` option:

.. include:: ../../examples/example_html.sh
    :code: bash
    :start-after: #BEGIN gcovr html
    :end-before: #END gcovr html

This generates a HTML summary of the lines executed.  In this
example, the file ``example1.html`` is generated, which has the
following output:

.. image:: ../../images/screenshot-html.png
    :align: center

The default behavior of the :option:`--html<gcovr --html>` option is to generate
HTML for a single webpage that summarizes the coverage for all files.  The
HTML is printed to standard output, but the :option:`-o/--output<gcovr --output>`
option is used to specify a file that stores the HTML output.

The :option:`--html-details<gcovr --html-details>` option is used to create
a separate web page for each file.  Each of these web pages includes
the contents of file with annotations that summarize code coverage.  Consider
the following command:

.. include:: ../../examples/example_html.sh
    :code: bash
    :start-after: #BEGIN gcovr html details
    :end-before: #END gcovr html details

This generates the following HTML page for the file ``example1.cpp``:

.. image:: ../../images/screenshot-html-details.example.cpp.png
    :align: center

Note that the :option:`--html-details<gcovr --html-details>` option needs
a named output, e.g. via the the :option:`-o/--output<gcovr --output>` option.
For example, if the output is named ``coverage.html``,
then the web pages generated for each file will have names of the form
``coverage.<filename>.html``.

The :option:`--html-self-contained<gcovr --html-self-contained>` option controls
whether assets like CSS styles are bundled into the HTML file.
The :option:`--html<gcovr --html>` report defaults to self-contained mode.
but :option:`--html-details<gcovr --html-details>` defaults to
:option:`--no-html-self-contained<gcovr --html-self-contained>`
in order to avoid problems with the `Content Security Policy <CSP_>`_
of some servers, especially Jenkins.

.. _CSP: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP

.. versionadded:: 5.0
   Added :option:`--html-self-contained<gcovr --html-self-contained>`
   and :option:`--no-html-self-contained<gcovr --html-self-contained>`.

.. versionchanged:: 5.0
   Default to external CSS file for :option:`--html-details<gcovr --html-details>`.
