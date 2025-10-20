#include <iostream>

#if defined USE_LAMBDA
# include <algorithm>
# include <array>
# include <functional>
#endif

int /* GCOVR_EXCL_FUNCTION */ foo(int param) { // GCOVR_EXCL_FUNCTION
   if (param) {
      param++;
   } else {
      param--;
   }

   return param;
}

int bar(int param) { // Excluded by CLI option
   if (param) {
      param++;
   } else {
      param--;
   }
   return param;
}

#if defined USE_LAMBDA
#define LAMBDA_SORT \
   { \
      std::array<int, 10> arr = { 0, 9, 1, 8, 2, 7, 3, 6, 4, 5 }; \
      std::sort( \
         std::begin(arr), \
         std::end(arr), \
         [](int a, int b) { \
            if (a > b) \
               return true; \
            return false; \
         } \
      ); \
   }

// Function in line with exclude
void sort_excluded(void) /* GCOVR_EXCL_FUNCTION */ { LAMBDA_SORT /* THIS is not excluded*/
   LAMBDA_SORT
}

void sort_lambda_excluded(void)
{
   LAMBDA_SORT // GCOVR_EXCL_FUNCTION not working because after function definition

   std::array<int, 10> arr = { 0, 9, 1, 8, 2, 7, 3, 6, 4, 5 };

   std::sort(
      std::begin(arr),
      std::end(arr),
      [](int a, int b) { // GCOVR_EXCL_FUNCTION
         if (a > b)
            return true;

         return false;
      }
   );
}

void sort_excluded_both(void) // GCOVR_EXCL_FUNCTION
{
   std::array<int, 10> arr = { 0, 9, 1, 8, 2, 7, 3, 6, 4, 5 };

   std::sort(
      std::begin(arr),
      std::end(arr),
      [](int a, int b) { // GCOVR_EXCL_FUNCTION
         if (a > b)
            return true;

         return false;
      }
   );

   std::sort(
      std::begin(arr),
      std::end(arr),
      [](int a, int b) { // Excluded by CLI option
         if (a > b)
            return true;

         return false;
      }
   );
}
#endif


int main(int argc, char* argv[]) {
   foo(0);
   bar(0);
#if defined USE_LAMBDA
   sort_excluded();
   sort_lambda_excluded();
   sort_excluded_both();
#endif
   return 0;
}
