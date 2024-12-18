#include <iostream>
#include <cstring>

extern int foo(int param);
extern int bar(int param);

class Bar
{
public:
    Bar() : m_param(1)
    {}
    virtual ~Bar()
    {} // possible compiler-generated destruction code - auto-detected and excluded

private:
    int m_param;
};

int main(int argc, char* argv[]) {
  for (int i = 0; i < 5; i++) { // 2/2 branches
    foo(i);
  }

  try {
    Bar bar; // LCOV_EXCL_LINE
  } catch (const std::exception &e) { // LCOV_EXCL_START
    std::cout << "caught exception";
    std::cout << ": " << e.what();
    std::cout << std::endl;
  } // LCOV_EXCL_STOP

  return 0;
} // compiler-generated destruction code - auto-detected and excluded

// total: 8/10 branches reported

