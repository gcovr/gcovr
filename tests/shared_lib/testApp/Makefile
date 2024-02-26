CFLAGS=-fprofile-arcs -ftest-coverage

all: test/a.out

test/a.out: tmp.cpp
	mkdir $(dir $@)
	$(CXX) $(CFLAGS) -I../lib/ $^ -o $@ -L../lib -ls

clean:
	rm -rf test
	rm -f *.gc*
