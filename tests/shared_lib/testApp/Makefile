
all: test/a.out

test/a.out: tmp.cpp
	mkdir $(dir $@)
	$(CXX) $(CXXFLAGS) -I../lib/ $^ -o $@ -L../lib -ls

clean:
	rm -rf test
	rm -f *.gc*
