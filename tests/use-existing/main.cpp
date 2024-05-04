#include <iostream>


int foo(int param) {
  if (param) {
     return 1; //std::cout << "param not null." << std::endl;
  } else {
     return 0; //std::cout << "param is null." << std::endl;
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
