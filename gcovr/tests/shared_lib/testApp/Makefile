CFLAGS=-fprofile-arcs -ftest-coverage

all: test/a.out

test/a.out: tmp.cpp
	$(CXX) $(CFLAGS) -I../lib/ $^ -o $@ -L../lib -ls
