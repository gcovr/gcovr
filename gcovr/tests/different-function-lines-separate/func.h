
#ifdef FOO_OTHER_LINE
int foo(int param) {
#else
int foo(int param) {
#endif
  if (param) {
     return 1;
  } else {
     return 0;
  }
}
