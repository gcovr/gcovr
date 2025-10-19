
inline int foo(int x) __attribute__((always_inline));
inline int foo(int x) {
  return x ? 1 : 0;
}

int main() {
    return foo(0);
}
