#include <iostream>

extern int foo(int param);
extern int bar();
extern int four_bar();
extern int uncovered();


int main(int argc, char* argv[]) {
  foo(0);
  bar();
  four_bar();

  return 0;
}
