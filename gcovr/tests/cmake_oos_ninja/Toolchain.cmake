set(CMAKE_SYSTEM_NAME GNU)

set(CMAKE_C_COMPILER $ENV{CC})
set(CMAKE_CXX_COMPILER $ENV{CXX})

add_compile_options( --coverage )
add_link_options( --coverage )