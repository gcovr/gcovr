#include <iostream>


int foo(int param) {
   if (param) { // GCOVR_EXCL_BR_LINE
      param++;
   } else {
      param--;
   }
   if (param) {
      param++;
   } else {
      param--;
   }
   // GCOV_EXCL_BR_START
   if (param) {
      param++;
   } else {
      param--;
   }
   // GCOV_EXCL_BR_STOP
   return param;
}


int main(int argc, char* argv[]) {
  foo(0);

  return 0;
}
