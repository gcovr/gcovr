CFLAGS=-fprofile-arcs -ftest-coverage

all: test/a.out

test/a.out: tmp.cpp
	g++ $(CFLAGS) -I../lib/ $^ -o $@ -L../lib -ls
