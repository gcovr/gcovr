#include <iostream>

class Bar
{
public:
    Bar()
    {}
    virtual ~Bar()
    {} // possible compiler-generated destruction code - auto-detected and excluded

private:
    int m_param;
};

int foo(int param) {
  if (param == 0 || param == 1) { // 4/4 branches
     return 1;
  } else if (param == 2 || param == 5) { // 3/4 branches, excluded, GCOV_EXCL_LINE
     return 0;
  } else if (param == 10) { // 1/2 branches
    return 2;
  } else if (param == 11) { // 1/2 branches
    return 3;
  }

  // GCOV_EXCL_START
  if (param == 4) { // 2/2 branches, excluded
     return 1;
  } else if (param == 5) { // 1/2 branches, excluded
     return 0;
  }
  // GCOV_EXCL_STOP

  return 0;
}


int main(int argc, char* argv[]) {
  for (int i = 0; i < 5; i++) { // 2/2 branches
    foo(i);
  }

  Bar bar;

  return 0;
} // compiler-generated destruction code - auto-detected and excluded

// total: 8/10 branches reported

