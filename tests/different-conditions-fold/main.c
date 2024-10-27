#include <stdio.h>

int foo(int param, int param2) {
  if (param != 0) {
     return 1;
  } else {
     return 0;
  }
}

int main(int argc, char* argv[]) {
  foo(0, 1);

  return 0;
}
