Gcovr Cookbook
==============

Python with C Extensions
------------------------

Collecting code coverage data on the C code that makes up a Python
extension module is not quite as straight forward as with a regular C
program.

There are two main steps that have to happen, first the
`-coverage` flag must be added into the compilation process this can be
easily accomplished by running `export CFLAGS="-coverage"` prior to
running `python setup.py build_ext`.

The second issue is that when extension modules share source code files,
the `build_ext` command will *always* rebuild them
regardless if the current object file is up to date.
This causes errors in the timestamps gcov uses to determine
if the proper notes and data exist.
It is nontrivial to implement a modified `build_ext` command to correct this,
instead using an external tool is the easier route.
The `ccache` utility works well on Unix based systems,
it also helps speed up the build process.
Running `export CC="ccache gcc"` will allow the "build_ext" command to use the two together.
It is important to note that if the same source file is recompiled
with a set of flags that cause it to be fundamentally different
(i.e. different macro definitions)
then this method may cause compilation errors.

In conclusion the following snippet will allow you to build your module
to collect coverage data.

.. code-block:: bash

    # Set required env vars
    export CFLAGS="-coverage"
    export CC="ccache gcc"
    # clear out build files so we get a fresh compile
    rm -rf build/temp.*
    rm -rf build/lib.*
    # rebuild extensions
    python setup.py build_ext --inplace
    # run test command i.e. pytest
    # build coverage data i.e. using ./bin/gcov.py shown below

After building your files using the method above
the \*.gcno and \*.gcda files are written to a temp.\* directory under `build`
instead of being part of the actual source code tree.
The code snippet below is a suitable Python script
to collect the files and manage the output files intelligently.
In this example the script is saved as ``./bin/gcov.py``.

.. code-block:: python

    #!/usr/bin/env python
    r"""
    Processes the coverage data generated for the C extensions using gcov.

    The extension should have been compiled with the -coverage flag which can
    be applied with `export CFLAGS="-coverage"` prior to building the extension
    modules. If you need to rebuild everything with the coverage flag use the
    command `python setup.py build_ext --inplace -f` or remove the build files
    under the build directory.

    Additionally, Python will rebuild any shared source files regardless if
    they have been compiled already or not. Using a tool such as `ccache` fixes
    this problem. The source cache program can be applied to gcc using
    `export CC="ccache gcc"`. Otherwise gcov will throw an error for "old"
    objects and coverage data will be inaccurate.

    Coverage collection example:
    ---
    export CFLAGS="-coverage"
    export CC="ccache gcc"
    rm -rf build
    python setup.py build_ext --inplace
    pytest
    ./bin/gcov.py
    ---
    """
    from glob import glob
    import os
    from subprocess import run
    from shutil import move, rmtree


    PROJ_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
    MODULE_SRC_DIR = src
    COVERAGE_DIR = os.path.join(PROJ_DIR, 'coverage')
    GCOV_CMD = [
        'gcov',
        '-pbc'
    ]
    GCOVR_INDEX_FILE = os.path.join(COVERAGE_DIR, 'index.html')
    GCOVR_CMD = [
        'gcovr',
        '--print-summary',
        '--html',
        '--html-details',
        '--keep',
        '--filter', MODULE_SRC_DIR,
        '-o', GCOVR_INDEX_FILE
    ]


    # collect all of the notes files
    build_dir = os.path.join(os.path.realpath('build'), 'temp.*')
    gcno_files = glob(os.path.join(build_dir, '**', '*.gcno'), recursive=True)


    # Create or recreate coverage directory
    try:
        os.mkdir(COVERAGE_DIR)
    except FileExistsError:
        rmtree(COVERAGE_DIR)
        os.mkdir(COVERAGE_DIR)


    # Run gcov or gcovr to calculate coverage totals
    try:
        run(GCOVR_CMD, check=True)
        print('View HTML report at: ' + GCOVR_INDEX_FILE)
    except FileNotFoundError as err:
        run(GCOV_CMD + gcno_files, check=True)
        print(err)
        print('"gcovr" is not installed no HTML report will be generated.')


    # Reconstruct source directory structure and move gcov files
    for file_name in glob('*.gcov'):
        abs_path = file_name.replace('#', os.path.sep)
        # Check if path is inside project's directory
        if PROJ_DIR not in abs_path:
            os.remove(file_name)
            continue
        rel_path = os.path.relpath(abs_path, PROJ_DIR)
        # create directories if needed and move file
        outfile = os.path.join(COVERAGE_DIR, rel_path)
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        move(file_name, outfile)
