cmake_minimum_required(VERSION 3.15)
project("GCOVR Example"
        LANGUAGES CXX)

#BEGIN cmakecmds
add_compile_options("--coverage")
add_link_options("--coverage")
#END cmakecmds

add_executable(program example.cpp)
