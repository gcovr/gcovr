This directory supports the creation of the Gcovr User Guide using
asciidoc and a2x commands.

HTML

The command

    make html

creates the guide.html file.


PDF

The command

    make pdf

creates the guide.tex file, which generates the guide.pdf file using
dblatex.



EPUB

The command

    make epub

creates the file make.epub.  Note that the `catalog.xml` file is
used, which configures asciidoc to use the docbook XML data in the
`epub` directory.  This is a bit of a hack.  It apparently works
around a limitation of the MacPorts installation of asciidoc.



NOTE: when updating the version of gcovr, the following files need to
be manually updated:

gcovr/doc/examples/example2.txt:

    cd gcovr/doc/examples
    lbin ./example2.sh > example2.txt

gcovr/doc/examples/example1.png:
    cd gcovr/doc/examples
    lbin ./example4.sh
    open example1.html
    <Capture this HTML page and save in the example1.png file.>
    convert example1.png -resize 700x700 example1.png

examples/example2_example2_cpp.png:
    cd gcovr/doc/examples
    lbin ./example5.sh
    cd example2
    open example2.html
    <Click example2.cpp link>
    <Capture this HTML page and save in the example2_example2.cpp.png file.>
    convert example2_example2_cpp.png -resize 700x900 example2_example2_cpp.png
    


