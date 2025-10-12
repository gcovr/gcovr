int foo(int param0, int param1) {
  if (param0 && param1) {
    return 1;
  } else {
    return 0;
  }
}

int main(int argc, char* argv[]) {
  foo(0, 0);

  return 0;
}
