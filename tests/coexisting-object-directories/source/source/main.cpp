#include <iostream>
int main () {
#if defined(ODD)
	std::cerr << "ODD\n";
   extern void fn_00 ();
   fn_00 ();
   extern void fn_01 ();
   fn_01 ();
   extern void fn_02 ();
   fn_02 ();
   extern void fn_03 ();
   fn_03 ();
   extern void fn_04 ();
   fn_04 ();
#else
	std::cerr << "EVEN\n";
   extern void fn_05 ();
   fn_05 ();
   extern void fn_06 ();
   fn_06 ();
   extern void fn_07 ();
   fn_07 ();
   extern void fn_08 ();
   fn_08 ();
   extern void fn_09 ();
   fn_09 ();
#endif
}
