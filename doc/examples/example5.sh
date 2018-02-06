#!/bin/bash

export PATH=`pwd`/../../scripts:$PATH

cd example1
ROOT=`pwd`

# @compile:
g++ -fprofile-arcs -ftest-coverage -fPIC -O0 example1.cpp -o program
# @:compile

# @run:
./program
# @:run

# @gcovr:
gcovr -r . --html --html-details -o example2.html
# @:gcovr

\rm -f program *.gc*
