#!/usr/bin/env bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr --txt-metric branch --txt example_branches.txt
#END gcovr

rm -f program *.gc*
