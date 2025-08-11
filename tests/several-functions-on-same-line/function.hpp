
void FUNCTION_NAME(int a, int b) {
   if ((a>=0) && (b<=10)) {
      std::cout << "Hello from if";
   }
   else {
      std::cout << "Hello from else";
   }
   std::cout << " (" << TO_STR(FUNCTION_NAME) << ")." << std::endl;
}

namespace ns {
   void FUNCTION_NAME(int a) {
      std::cout << "Hello from ns::" << TO_STR(FUNCTION_NAME) << "." << std::endl;
   }
}
