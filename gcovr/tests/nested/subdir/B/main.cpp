#include <iostream>

extern int foo(int param);
extern int bar();


int main(int argc, char* argv[]) {
  foo(0);
  bar();

  return 0;
}
