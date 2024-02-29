#include <iostream>
#include <stdlib.h>

__attribute__((__noreturn__))
static void panic(void)
{
  abort();
}

int foo(int param)
{
  if (param > 1) {
    return 3;
  }

  panic();
}


int main(int argc, char* argv[]) {
  foo(2);

  return 0;
}
