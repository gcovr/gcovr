This directory supports the creation of the Gcovr User Guide using
docutils (`rst2html5.py`).

The command

    make html

creates the guide.html file.

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
