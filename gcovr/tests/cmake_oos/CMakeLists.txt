
cmake_minimum_required(VERSION 2.6.4 FATAL_ERROR)

project(gcovrtest)

# Previously, this would only add the coverage flags under UNIX. That is
# wrong, because the flags don't depend on the platform but on the compiler.
# Because gcovr only supports GCC and compatible (i.e. Clang), no check is
# necessary – when the flags don't work, the tests should fail!

set(CMAKE_BUILD_TYPE DEBUG)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O0 -Wall -fprofile-arcs -ftest-coverage ")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O0 -Wall -fprofile-arcs -ftest-coverage ")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage ")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage ")


add_executable(gcovrtest main.cpp)

