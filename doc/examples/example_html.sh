#!/bin/bash

export PATH=`pwd`/../../scripts:$PATH

g++ -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr html
gcovr -r . --html -o example-html.html
#END gcovr html

#BEGIN gcovr html details
gcovr -r . --html --html-details -o example-html-details.html
#END gcovr html details

rm -f program *.gc*
