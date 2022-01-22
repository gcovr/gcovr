.. _cookbook:

Cookbook
========

This section contains how-to guides
on creating code coverage reports for various purposes.
For an introduction on using gcovr,
see the :ref:`guide` instead.

Recipes in the cookbook:

.. contents::
   :local:
   :depth: 1

.. _c extensions in python:

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
    gcovr --filter src/ --print-summary --html-details coverage/index.html

.. _oos cmake:

Out-of-Source Builds with CMake
-------------------------------

Tools such as ``cmake`` encourage the use of out-of-source builds,
where the code is compiled in a directory other than the one which
contains the sources. This is an extra complication for ``gcov``.
In order to pass the correct compiler and linker flags, the following
commands need to be in ``CMakeLists.txt``:

.. include:: ../examples/CMakeLists.txt
    :code: cmake
    :start-after: #BEGIN cmakecmds
    :end-before: #END cmakecmds

The ``--coverage`` compiler flag is an alternative to
``-fprofile-arcs -ftest-coverage`` for
`recent version of gcc <https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html>`__.
In versions 3.13 and later of ``cmake``, the
``target_link_libraries`` command can be removed and
``add_link_options("--coverage")`` added after
the ``add_compile_options`` command.

We then follow a normal ``cmake`` build process:

.. include:: ../examples/example_cmake.sh
    :code: bash
    :start-after: #BEGIN cmake_build
    :end-before: #END cmake_build

and run the program:

.. include:: ../examples/example_cmake.sh
    :code: bash
    :start-after: #BEGIN cmake_run
    :end-before: #END cmake_run

However, invocation of ``gcovr`` itself has to change. The assorted
``.gcno`` and ``.gcda`` files will appear under the ``CMakeFiles``
directory in ``BLD_DIR``, rather than next to the sources. Since
``gcovr`` requires both, the command we need to run is:

.. include:: ../examples/example_cmake.sh
    :code: bash
    :start-after: #BEGIN cmake_gcovr
    :end-before: #END cmake_gcovr
