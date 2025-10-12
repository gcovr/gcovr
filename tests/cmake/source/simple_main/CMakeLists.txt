cmake_minimum_required(VERSION 3.12 FATAL_ERROR)

project(testcase)

    # This flags are used if cmake is called with -DCMAKE_BUILD_TYPE=PROFILE
    set(CMAKE_C_FLAGS_PROFILE --coverage)
    set(CMAKE_CXX_FLAGS_PROFILE --coverage)

    add_executable(testcase main.cpp)

