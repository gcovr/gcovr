#!/usr/bin/env bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr --cobertura-pretty --cobertura example_cobertura.xml
#END gcovr

rm -f program *.gc*

if [[ "$OSTYPE" != "msys" ]]; then
xmllint --noout --nowarning --dtdvalid $PWD/../../tests/cobertura.coverage-04.dtd example_cobertura.xml || exit 1
fi
