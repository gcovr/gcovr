#include <iostream>

class Bar
{
  public:
    Bar() : m_bar(1)
    {}
    virtual ~Bar()
    {} // possible compiler-generated destruction code - auto-detected and excluded

    void foo() const
    {
        std::cout << "Const " << this->m_bar << std::endl;
    }
    void foo()
    {
      std::cout << "Non const " << this->m_bar << std::endl;
    }

  private:
    int m_bar;
};

int main(int argc, char* argv[]) {
  Bar bar;
  const Bar const_bar;
  bar.foo();
  const_bar.foo();

  return 0;
}
