#include <iostream>

extern int foo(int param);
extern int foobar(int param);
extern int bar();
extern int four_bar();
extern int foo5(int param);
extern int foo6(int param);
extern int uncovered();


int main(int argc, char* argv[]) {
  foo(0);
  foobar(1);
  bar();
  four_bar();
  foo5(0);
  if (argc != 0) { if (argv[0] != 0) { foo6(0); } }

  return 0;
}
