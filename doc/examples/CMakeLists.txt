cmake_minimum_required(VERSION 3.12)
project("GCOVR Example"
        LANGUAGES CXX)

#BEGIN cmakecmds
add_compile_options("--coverage")

add_executable(program example.cpp)
target_link_libraries(program gcov)
#END cmakecmds
