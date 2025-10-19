#include <iostream>

void foo() {
   std::cout << "Hello from foo()." << std::endl;
}

template<typename T>
void func(T a, T b) {
   if (a < b) {
      std::cout << a << " is less than " << b << std::endl;
   }
}

#define TO_STR(x) #x

#define FUNCTION_NAME func_a
#include "function.hpp"
#undef FUNCTION_NAME

#define FUNCTION_NAME func_b
#include "function.hpp"
#undef FUNCTION_NAME

int main(int argc, char* argv[]) {
   foo();

   func_a(0, 0);
   func_a(-1, 0);
   func_a(1, 0);
   func_a(0, 11);
   ns::func_a(0);

   func_b(0, 0);
   ns::func_b(1);

   func<>(0, 0);
   func<>(0, 1);

   func<>(0.0, 0.0);
   func<>(0.0, -1.0);

   return 0;
}
