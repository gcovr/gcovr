#include <iostream>


int foo(int param) {
  if (param) {
     return 1; //std::cout << "param not null." << std::endl;
  } else {
     return 0; //std::cout << "param is null." << std::endl; GCOVR_EXCL_LINE
  }
  // LCOV_EXCL_START
  if (param) {
     return 1; //std::cout << "param not null." << std::endl;
  } else {
     return 0; //std::cout << "param is null." << std::endl;
  }
  // LCOV_EXCL_STOP
}

// LCOV_EXCL_START
int bar(void) {
   return 1;
}
// LCOV_EXCL_STOP

int main(int argc, char* argv[]) {
  foo(0);
  bar(); // GCOVR_EXCL_LINE

  return 0;
}
