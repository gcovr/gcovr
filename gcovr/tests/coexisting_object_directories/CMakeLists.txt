cmake_minimum_required(VERSION 3.14)

project(gcovr_parallel_calls LANGUAGES CXX)

set(CMAKE_CXX_FLAGS_PROFILE --coverage)

add_executable(parallel_call)

target_sources (parallel_call
	PRIVATE
	source/fn_00.cc
	source/fn_01.cc
	source/fn_02.cc
	source/fn_03.cc
	source/fn_04.cc
	source/fn_05.cc
	source/fn_06.cc
	source/fn_07.cc
	source/fn_08.cc
	source/fn_09.cc
	source/main.cc)

if(ODD)
	target_compile_definitions (parallel_call PRIVATE ODD)
endif()

