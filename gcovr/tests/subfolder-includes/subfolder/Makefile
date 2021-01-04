all: subfolder/testcase

subfolder/testcase:subfolder/main.o subfolder/lib.o
	$(CXX) -fprofile-arcs -ftest-coverage -o $@ $^

.cpp.o:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -c -I../include -o $@ $^

clean:
	rm -f subfolder/testcase
	rm -f subfolder/*.gc*
	rm -f subfolder/*.o