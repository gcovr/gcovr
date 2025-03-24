#include <iostream>


int foo(int param) {
   if (param) { // GCOVR_EXCL_BR_LINE
      param++; //std::cout << "param not null." << std::endl;
   } else {
      param--; //std::cout << "param is null." << std::endl;
   }
   if (param) { 
      param++; //std::cout << "param not null." << std::endl; 
   } else {
      param--; //std::cout << "param is null." << std::endl;
   }
   // GCOV_EXCL_BR_START
   if (param) {
      param++; //std::cout << "param not null." << std::endl;
   } else {
      param--; //std::cout << "param is null." << std::endl;
   }
   // GCOV_EXCL_BR_STOP
   return param;
}


int main(int argc, char* argv[]) {
  foo(0);

  return 0;
}
