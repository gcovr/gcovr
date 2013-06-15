#include <iostream>

extern int foo(int param);
extern int foobar(int param);
extern int bar();
extern int fourbar();


int main(int argc, char* argv[]) {
  foo(0);
  foobar(1);
  bar();
  fourbar();

  return 0;
}
