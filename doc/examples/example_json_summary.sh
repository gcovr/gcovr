#!/bin/bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr --json-summary-pretty --json-summary example_json_summary.json
#END gcovr

rm -f program *.gc*
