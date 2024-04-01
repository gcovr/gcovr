#!/usr/bin/env bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr --csv example_csv.csv
#END gcovr

rm -f program *.gc*
