
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

int bar(int param) { // never called, GCOV_EXCL_START
  if (param) {
    return 1;
  }
  return 0;
} // GCOV_EXCL_STOP
