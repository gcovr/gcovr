all: testcase

testcase:main.o lib.o
	$(CXX) -fprofile-arcs -ftest-coverage -o $@ $^

.cpp.o:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -c -I../include -o $@ $^

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f *.o