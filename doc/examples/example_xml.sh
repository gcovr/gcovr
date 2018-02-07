#!/bin/bash

export PATH=`pwd`/../../scripts:$PATH

g++ -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr -r . --xml-pretty
#END gcovr

rm -f program *.gc*
