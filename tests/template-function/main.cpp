
#include <iostream>

template<typename T>
void foo(T s)
{
  static int i = 0;

  if (i >= 0) {
    std::cout << i << " is greater or equal 0: " << s << std::endl;
  }
  if (i > 0) if ( i < 2 || i > 4 ) std::cout << i << " is between 0 and 2 or greater 4: " << s << std::endl;
  if (i >= 5) {
    std::cout << i << " is greater 5: " << s << std::endl;
  }

  ++i;
}

void bar()
{
  static int i = 0;

  if (i >= 0) {
    std::cout << i << " is greater or equal 0" << std::endl;
  }
  if (i > 0) if ( i < 2 || i > 4 ) std::cout << i << " is between 0 and 2 or greater 4" << std::endl;
  if (i >= 5) {
    std::cout << i << " is greater 5"<< std::endl;
  }

  ++i;
}

int main() {
  foo<>(0);
  foo<>(0);
  foo<>(0);
  foo<>(0);
  foo<>(0);
  foo<>(0);

  foo<>(0.0);
  foo<>(0.0);
  foo<>(0.0);
  foo<>(0.0);

  bar();
  bar();
  bar();
  bar();

  return 0;
}
