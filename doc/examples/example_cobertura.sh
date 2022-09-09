#!/bin/bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr --cobertura-pretty
#END gcovr

if [[ "$OSTYPE" != "msys" ]]; then
xmllint --valid --noout example_cobertura.xml || exit 1
fi

rm -f program *.gc*
