#include <iostream>

int foo(int param) {
   // GCOVR_EXCL_BR_SOURCE: No information
   switch (param) {
   case 0:
      return 1;
   case 1:
      return 2;
   case 2:
      return 3; // GCOVR_EXCL_BR_SOURCE
   case 3:
      return 4;
   default:
      return 0; // GCOVR_EXCL_BR_SOURCE
   }
}

int main(int argc, char* argv[]) { // GCOVR_EXCL_BR_SOURCE: No blocks
   if (foo(0) && foo(3)) {
      std::cout << "True" << std::endl;
   }
   else {
      std::cout << "False" << std::endl; // GCOVR_EXCL_BR_SOURCE
   }

   return 0;
}
