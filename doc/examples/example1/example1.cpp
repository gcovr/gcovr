// example1.cpp

#include <iostream>

#define MACRO()   if (1<0) foo(-1); else foo(1);

int foo(int param)
{
    if (param)
    {
        return 1;
    }
    else
    {
        return 0;
    }
}

void bar(int param)
{
    if (param)
    {
        std::cout << "param not null." << std::endl;
    }
    else
    {
        std::cout << "param is null." << std::endl;
    }
}


int main(int argc, char* argv[])
{
    MACRO()

    foo(0);

    return 0;
}

