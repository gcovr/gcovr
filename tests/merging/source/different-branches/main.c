
#include <iostream>
#ifdef TWO_CONDITIONS
 #define CONDITION (argc > 0) && (argc <=1)
#else
 #define CONDITION (argc > 0)
#endif
#define TO_STR(x) #x

int main(int argc, char* argv[]) {
  std::cout << TO_STR(CONDITION) << ": ";
  if (CONDITION) {
    std::cout << "True";
  }
  else {
    std::cout << "False";
  }
  std::cout << std::endl;

  return 0;
}
