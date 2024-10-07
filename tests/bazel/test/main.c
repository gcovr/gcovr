
#include "lib.h"

int main() {
    return foo(1) || foo(3)
        ? 0
        : 1;
}
