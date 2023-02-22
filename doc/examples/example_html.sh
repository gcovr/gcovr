#!/bin/bash
set -euo pipefail  # "use strict"

# This file is used both as an example and as a test.
# In order to get reproducible tests,
# this function wraps gcovr to force a specific timestamp.
# This can be ignored by end users and isn't really part of the example.
gcovr() {
    export SOURCE_DATE_EPOCH=3666
    python3 -m gcovr "$@"
    unset SOURCE_DATE_EPOCH
}


${CXX:-g++} -fprofile-arcs -ftest-coverage -fPIC -O0 example.cpp -o program

./program

#BEGIN gcovr html
gcovr --html
#END gcovr html

#BEGIN gcovr html details
gcovr --html-details example_html.details.html
#END gcovr html details

#BEGIN gcovr html nested
gcovr --html-nested example_html.nested.html
#END gcovr html nested

rm -f program *.gc* example_html.nested*.*
