cmake_minimum_required(VERSION 3.14)

project(gcovr_parallel_calls LANGUAGES CXX)

set(CMAKE_CXX_FLAGS_PROFILE --coverage)

add_executable(parallel_call)

target_sources (parallel_call
	PRIVATE
	source/fn_00.cpp
	source/fn_01.cpp
	source/fn_02.cpp
	source/fn_03.cpp
	source/fn_04.cpp
	source/fn_05.cpp
	source/fn_06.cpp
	source/fn_07.cpp
	source/fn_08.cpp
	source/fn_09.cpp
	source/main.cpp)

if(ODD)
	target_compile_definitions (parallel_call PRIVATE ODD)
endif()

