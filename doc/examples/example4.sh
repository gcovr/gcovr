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
gcovr -r . --html -o example1.html
# @:gcovr
mv example1.html ..

\rm -f program *.gc*
