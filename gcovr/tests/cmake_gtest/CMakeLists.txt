cmake_minimum_required(VERSION 3.14)

project(gcovr_gtest)

  # This flags are used if cmake is called with -DCMAKE_BUILD_TYPE=PROFILE
  set(CMAKE_C_FLAGS_PROFILE --coverage)
  set(CMAKE_CXX_FLAGS_PROFILE --coverage)

  # GoogleTest requires at least C++14
  set(CMAKE_CXX_STANDARD 14)

  add_executable(
    gcovr_gtest
    test/test.cpp
    source/code.cpp
  )
  target_link_libraries(
    gcovr_gtest
    gtest
    pthread
  )
