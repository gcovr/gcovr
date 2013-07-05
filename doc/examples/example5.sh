#!/bin/bash

. GetGlobals.sh
export PATH=$CXXTEST/bin:$PATH:`pwd`/../../scripts

cd example2
ROOT=`pwd`

# @compile:
g++ -fprofile-arcs -ftest-coverage -fPIC -O0 example2.cpp -o program
# @:compile

# @run:
./program
# @:run

# @gcovr:
gcovr -r . --html --html-details -o example2.html
# @:gcovr
mv example2.html ..

\rm -f program *.gc*
