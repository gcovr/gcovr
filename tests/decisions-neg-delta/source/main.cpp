#include <vector>

class Foo {
public:
  void work(int arg) {
    if (arg < 2) {
      std::vector<int> tmp{0, 0};
      for (int i : tmp) {
      }
    }
  }
};

int main(int argc, char **argv) {
  Foo foo;
  foo.work(1);
  return 0;
}