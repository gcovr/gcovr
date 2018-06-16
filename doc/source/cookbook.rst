Gcovr Cookbook
==============

How to collect coverage for C extensions in Python
--------------------------------------------------

Collecting code coverage data on the C code that makes up a Python
extension module is not quite as straightforward as with a regular C
program.

As with a normal C project,
we have to compile our code with coverage instrumentation.
Here, we ``export CFLAGS="--coverage"``
and then run ``python3 setup.py build_ext``.

Unfortunately, ``build_ext`` can rebuild a source file
even if the current object file is up to date.
If multiple extension modules share the same source code file,
gcov will get confused by the different timestamps
and report inaccurate coverage.
It is nontrivial to adapt the ``build_ext`` process to avoid this.

Instead, we can use the ``ccache`` utility to make the compilation lazy
(works best on Unix systems).
Before we invoke the ``build_ext`` step, we first ``export CC="ccache gcc"``.
Ccache works well but isn't absolutely perfect,
see the `ccache manual`_ for caveats.

.. _ccache manual: https://ccache.samba.org/manual/latest.html#_caveats

A shell session might look like this:

.. code-block:: sh

    # Set required env vars
    export CFLAGS="--coverage"
    export CC="ccache gcc"

    # clear out build files so we get a fresh compile
    rm -rf build/temp.*  # contains old .gcda, .gcno files
    rm -rf build/lib.*

    # rebuild extensions
    python3 setup.py build_ext --inplace  # possibly --force

    # run test command i.e. pytest

    # run gcovr
    rm -rf coverage; mkdir coverage
    gcovr --filter src/ --print-summary --html-details -o coverage/index.html
