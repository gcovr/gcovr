#!/usr/bin/env bash

rm -fr build
mkdir build
cd build
cmake ..
make

testcase


