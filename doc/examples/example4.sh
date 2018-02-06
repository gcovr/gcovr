#!/bin/bash

export PATH=$PATH:`pwd`/../../scripts

cd example1
ROOT=`pwd`

# @compile:
g++ -fprofile-arcs -ftest-coverage -fPIC -O0 example1.cpp -o program
# @:compile

# @run:
./program
# @:run

# @gcovr:
../../../scripts/gcovr -r . --html -o example1.html
# @:gcovr
mv example1.html ..

\rm -f program *.gc*
