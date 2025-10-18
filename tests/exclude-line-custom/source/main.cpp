#include <iostream>


int foo(int param) {
  if (param) {
    // LCOV_EXCL_START
    std::cout << "param not null in block markers" << std::endl;
    // LCOV_EXCL_STOP

    // CUSTOM_EXCL_START
    std::cout << "param not null in block markers" << std::endl;
    // CUSTOM_EXCL_STOP

     std::cout << "param not null" << std::endl; // CUSTOM_EXCL_LINE
     return 1; // GCOVR_EXCL_LINE
  } else {
    // LCOV_EXCL_START
    std::cout << "param is null in block markers" << std::endl;
    // LCOV_EXCL_STOP

    // CUSTOM_EXCL_START
    std::cout << "param is null in block markers" << std::endl;
    // CUSTOM_EXCL_STOP

     std::cout << "param is null" << std::endl; // CUSTOM_EXCL_LINE
     return 0; // GCOVR_EXCL_LINE
  }
}


int main(int argc, char* argv[]) {
  foo(0);

  return 0;
}
