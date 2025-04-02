#include <iostream>

namespace ns1
{
  class Bar1
  {
    public:
      Bar1() : m_bar_1(1)
      { ++m_counter_bar1; }
      virtual ~Bar1()
      { --m_counter_bar1; } // possible compiler-generated destruction code - auto-detected and excluded

      int m_bar_1;
      static int m_counter_bar1;
  };
  int Bar1::m_counter_bar1 = 0;
}

namespace ns2
{
  class Bar2 : public ns1::Bar1
  {
    public:
      Bar2() : m_bar_2(2)
      { ++m_counter_bar2; }
      virtual ~Bar2()
      { --m_counter_bar2; } // possible compiler-generated destruction code - auto-detected and excluded

      int m_bar_2;
      static int m_counter_bar2;
  };
  int Bar2::m_counter_bar2 = 0;
}

namespace ns3
{
  class Bar3 : public ns2::Bar2
  {
    public:
      Bar3() : m_bar_3(3)
      { ++m_counter_bar3; }
      virtual ~Bar3()
      { --m_counter_bar3; } // possible compiler-generated destruction code - auto-detected and excluded

      int m_bar_3;
      static int m_counter_bar3;
  };
  int Bar3::m_counter_bar3 = 0;
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
