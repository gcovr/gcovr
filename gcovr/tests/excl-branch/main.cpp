#include <iostream>


int foo(int param) {
  if (param) { // GCOVR_EXCL_BR_LINE
     return 1; //std::cout << "param not null." << std::endl;
  } else {
     return 0; //std::cout << "param is null." << std::endl;
  }
  if (param) { 
     return 1; //std::cout << "param not null." << std::endl; 
  } else {
     return 0; //std::cout << "param is null." << std::endl;
  }
  // GCOV_EXCL_BR_START
  if (param) {
     return 1; //std::cout << "param not null." << std::endl;
  } else {
     return 0; //std::cout << "param is null." << std::endl;
  }
  // GCOV_EXCL_BR_STOP
}


int main(int argc, char* argv[]) {
  foo(0);

  return 0;
}
