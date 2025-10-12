#include <iostream>

#ifdef FOO
  extern int foo();
#endif
#ifdef BAR
  extern int bar();
#endif

int main(int argc, char* argv[]) {
#ifdef FOO
  foo();
#endif
#ifdef BAR
  bar();
#endif

  return 0;
}
