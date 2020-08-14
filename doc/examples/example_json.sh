#!/bin/bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr -r . --coveralls example_json.json
#END gcovr

rm -f program *.gc*
