#include <iostream>
#include <cstdlib>

int main(int argc, char* argv[]) {
   try {
      std::cout << "Exit program" << std::endl;
      std::exit(0);
   }
   catch (const std::exception& e) {
      // Do nothing
   }
}
