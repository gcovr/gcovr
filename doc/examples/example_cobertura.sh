#!/usr/bin/env bash

${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr
gcovr --cobertura-pretty --cobertura example_cobertura.xml
#END gcovr

rm -f program *.gc*
sed -e 's/\(<source>\).*\/\(doc\/\)/\1\2/' example_cobertura.xml > example_cobertura.xml.patched
mv -f example_cobertura.xml.patched example_cobertura.xml
