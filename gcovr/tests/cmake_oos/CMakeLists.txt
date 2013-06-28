
cmake_minimum_required(VERSION 2.6.4 FATAL_ERROR)

project(gcovrtest)

if (UNIX)
  set(CMAKE_BUILD_TYPE DEBUG)
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O0 -Wall -fprofile-arcs -ftest-coverage ")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O0 -Wall -fprofile-arcs -ftest-coverage ")
  set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage ")
  set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage ")
else()
  message(STATUS "coverage flags not supported for this plaform.")
endif()


add_executable(gcovrtest main.cpp)

