#!/usr/bin/env bash
set -eo pipefail

# 1. Prepare the example workspace.

WORKSPACE=example_cmake_workspace
mkdir -p "$WORKSPACE"
rm -rf $WORKSPACE/*

# clean up afterwards, or else the *other* examples will fail.
trap 'rm -rf $WORKSPACE/*' EXIT ERR

mkdir $WORKSPACE/src $WORKSPACE/bld
# Path variables.
# The SRC_DIR would usually be an absolute path,
# but that would prevent the tests from being reproducible.
# As that variable is only used from within the BLD_DIR,
# we can hardcode it here.
BLD_DIR="$(cd $WORKSPACE/bld; pwd)"
SRC_DIR=../src
cp example.cpp CMakeLists.txt $WORKSPACE/src

# 2. Build the software.
(
exec >&2  # redirect output to STDERR

#BEGIN cmake_build
cd $BLD_DIR
cmake -DCMAKE_BUILD_TYPE=PROFILE $SRC_DIR
cmake --build . --verbose
#END cmake_build
)

# 3. Execute the program.
(
exec >&2  # redirect output to STDERR

#BEGIN cmake_run
cd $BLD_DIR
./program
#END cmake_run
)

# 4. Execute gcovr.
(
#BEGIN cmake_gcovr
cd $BLD_DIR
gcovr -r $SRC_DIR . --txt ../../example_cmake.txt
#END cmake_gcovr
)
