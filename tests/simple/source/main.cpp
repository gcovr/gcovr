#include <iostream>

int not_called(void) {
   return 1;
}

int foo(int param) {
  if (param) {
     return 1;
  } else {
     return 0;
  }
}


int main(int argc, char* argv[]) {
  foo(
     0
     )
     ;
  if (argc > 1) {
     foo(
        1
        )
        ;
     }

  return 0;
}
