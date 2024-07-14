cmake_minimum_required(VERSION 3.12)
project("GCOVR Example"
        LANGUAGES CXX)

#BEGIN cmake_cmd
# This flags are used if cmake is called with -DCMAKE_BUILD_TYPE=PROFILE
set(CMAKE_C_FLAGS_PROFILE --coverage)
set(CMAKE_CXX_FLAGS_PROFILE --coverage)

add_executable(program example.cpp)
#END cmake_cmd
