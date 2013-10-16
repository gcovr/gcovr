CFLAGS=-fprofile-arcs -ftest-coverage
INSTALL ?= install -p

all: test/a.out

test/a.out: tmp.cpp
	$(INSTALL) -d $(dir $@)
	$(CXX) $(CFLAGS) -I../lib/ $^ -o $@ -L../lib -ls

clean:
	rm -rf test
	rm -f *.gc*
