#!/usr/bin/env bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr --clover-pretty --clover example_clover.xml
#END gcovr

rm -f program *.gc*
