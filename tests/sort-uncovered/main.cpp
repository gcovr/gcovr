#include <iostream>

extern int foo(int param);
extern int bar();
extern int fourbar();
extern int uncovered();


int main(int argc, char* argv[]) {
  foo(0);
  bar();
  fourbar();

  return 0;
}
