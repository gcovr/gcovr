#!/bin/bash

export PATH=`pwd`/../../scripts:$PATH

#BEGIN compile
g++ -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program
#END compile

#BEGIN run
./program
#END run

#BEGIN gcovr
gcovr -r .
#END gcovr

rm -f program *.gc*
