#include <iostream>

namespace
{
  class Bar
  {
    public:
      Bar() : m_bar(1)
      {}
      ~Bar()
      {}

      int foo(void) const
      {
        std::cout << "Const m_bar: " << this->m_bar << std::endl;
        return 0;
      }

      int m_bar;
  };
  int foo(void)
  {
    const Bar bar;
    return bar.foo();
  }
}

// The extern "C" results in missing braces in function
extern "C" int bar()
{
  return foo();
}

int bar_cpp()
{
  return bar();
}

int main(int argc, char* argv[]) {
  return bar_cpp();
}
