#!/bin/bash

. GetGlobals.sh
export PATH=$CXXTEST/bin:$PATH:`pwd`/../../scripts

cd example1
ROOT=`pwd`
echo $ROOT

# @compile:
g++ -fprofile-arcs -ftest-coverage -fPIC -O0 example1.cpp -o program
# @:compile

# @run:
./program
# @:run

gcovr -e /usr/include > ../example1.out
# @run:
gcovr -e /usr/include
# @:run
\rm -f program *.gc*
