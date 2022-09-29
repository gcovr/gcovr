#include <stdio.h>

int function1(void)
{
    printf("Inside function()\n");
    return 1;
}

int function2(void)
{
    printf("Inside function2()\n");
    return 1;
}

int function3(int a)
{
    printf("Inside function3()\n");
    return 1;
}

int main(int argc, char **argv)
{
    printf("test\n");
    int a = 0;
    int b = 0;
    int c = 0;

    for (a = 0; a < 2; a++) {
        for (b= 0; b < 2; b++) {
            c = 0;
            if (a > 0 && b > 0 || c > 0) {
                function2();
            } else {
                function1();
            }
            if (c > 0) {
                // Never called
                function3(function2());
                function2();
            }
            function2();
            function2();
            //    called                not called            called                not called
            if (((function1() == 1) || (function2()==1)) && ((function1() != 1) && (function2()!=1))) {
                // never called
                function2();
            }
        }
    }

    return 0;
}
