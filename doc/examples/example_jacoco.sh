#!/usr/bin/env bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr --jacoco-pretty --jacoco example_jacoco.xml
#END gcovr

rm -f program *.gc*

if [[ "$OSTYPE" != "msys" ]]; then
xmllint --noout --nowarning --dtdvalid $PWD/../../tests/JaCoCo.report.dtd example_jacoco.xml || exit 1
fi
