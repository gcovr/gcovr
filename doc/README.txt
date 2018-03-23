This directory supports the creation of the Gcovr User Guide using
sphinx.

The following python packages have to be installed, e.g. with pip:

    pip install sphinx sphinx_rtd_theme

The command

    make html

creates the documentation in the folder build/html.

When updating for a new gcovr version,
the screenshots will have to be regenerated.
If you have wkhtmltopdf installed, run

    make clean-images
    make

Otherwise:

1.  delete the examples/*.png files

2.  in the examples directory, run

        ./example_html.sh

3.  make screenshots of

        examples/example-html.html
        examples/example-html-details.example.cpp.html

4.  resize the screenshots to a maximum width of 700 pixels
