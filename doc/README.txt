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

        ./example4.sh
        ./example5.sh

3.  make screenshots of

        examples/example1.html
        examples/example1/example2.example1.cpp.html

4.  resize the screenshots to a maximum width of 700 pixels
