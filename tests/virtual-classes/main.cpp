#include <iostream>

namespace ns1
{
  class Bar1
  {
    public:
      Bar1() : m_bar_1(1)
      {}
      virtual ~Bar1()
      {} // possible compiler-generated destruction code - auto-detected and excluded

      int m_bar_1;
  };
}

namespace ns2
{
  class Bar2 : public ns1::Bar1
  {
    public:
      Bar2() : m_bar_2(2)
      {}
      virtual ~Bar2()
      {} // possible compiler-generated destruction code - auto-detected and excluded

      int m_bar_2;
  };
}

namespace ns3
{
  class Bar3 : public ns2::Bar2
  {
    public:
      Bar3() : m_bar_3(3)
      {}
      virtual ~Bar3()
      {} // possible compiler-generated destruction code - auto-detected and excluded

      int m_bar_3;
  };
}

int main(int argc, char* argv[]) {
  try {
    ns1::Bar1 bar1;
    std::cout << "bar1.m_bar_1: " << bar1.m_bar_1 << std::endl;
    ns2::Bar2 bar2;
    std::cout << "bar2.m_bar_1: " << bar2.m_bar_1 << std::endl;
    std::cout << "bar2.m_bar_2: " << bar2.m_bar_2 << std::endl;
    ns3::Bar3 bar3;
    std::cout << "bar3.m_bar_1: " << bar3.m_bar_1 << std::endl;
    std::cout << "bar3.m_bar_2: " << bar3.m_bar_2 << std::endl;
    std::cout << "bar3.m_bar_3: " << bar3.m_bar_3 << std::endl;
  } catch (const std::exception &e) { // LCOV_EXCL_START
    std::cout << "caught exception";
    std::cout << ": " << e.what();
    std::cout << std::endl;
  } // LCOV_EXCL_STOP

  return 0;
} // compiler-generated destruction code - auto-detected and excluded
