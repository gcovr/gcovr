#include <iostream>

extern int foo(int param);
extern int foobar(int param);
extern int bar();
extern int fourbar();
extern int foo5(int param);
extern int foo6(int param);


int main(int argc, char* argv[]) {
  foo(0);
  foobar(1);
  bar();
  fourbar();
  foo5(0);
  foo6(0);

  return 0;
}
