This directory supports the creation of the Gcovr User Guide using
asciidoc and a2x commands.

HTML

The command

    make html

creates the guide.html file.


NOTE: when updating the version of gcovr, the following files need to
be manually updated:

gcovr/doc/examples/example1.png:
    cd gcovr/doc/examples
    lbin ./example4.sh
    open example1.html
    <Capture this HTML page and save in the example1.png file.>
    convert example1.png -resize 700x700 example1.png

examples/example2_example1_cpp.png:
    cd gcovr/doc/examples
    lbin ./example5.sh
    cd example1
    open example2.html
    <Click example1.cpp link>
    <Capture this HTML page and save in the example2_example1.cpp.png file.>
    convert example2_example1_cpp.png -resize 700x900 example2_example1_cpp.png
    


