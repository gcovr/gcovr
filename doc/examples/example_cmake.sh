#!/bin/bash

export SRC_DIR=`pwd`
export BLD_DIR=/tmp/bld

mkdir $BLD_DIR

#BEGIN cmake_build
cd $BLD_DIR
cmake $SRC_DIR
make VERBOSE=1
#END cmake_build

#BEGIN cmake_run
./program
#END cmake_run

#BEGIN cmake_gcovr
gcovr -r $SRC_DIR $BLD_DIR
#END cmake_gcovr
