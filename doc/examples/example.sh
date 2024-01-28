#!/bin/bash

g++() {
	$(which ${CXX:-g++}) $*
}

#BEGIN compile
g++ -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program
#END compile

#BEGIN run
./program
#END run

#BEGIN gcovr
gcovr --txt example.txt
#END gcovr

rm -f program *.gc*
