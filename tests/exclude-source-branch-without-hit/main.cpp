#include <iostream>

int foo(int param) {
   // GCOVR_EXCL_BR_WITHOUT_HIT: 1/2: No information
   switch (param) { // GCOVR_EXCL_BR_WITHOUT_HIT: 3/5
   case 0:
      return 1;
   case 1:
      return 2;
   case 2:
      return 3;
   case 3:
      return 4;
   default:
      return 0;
   }
}

int main(int argc, char* argv[]) {
   if (foo(0) && foo(3)) { // GCOVR_EXCL_BR_WITHOUT_HIT: 2/6
      std::cout << "True" << std::endl;
   }
   else {
      std::cout << "False" << std::endl;
   }

   return 0;
}
