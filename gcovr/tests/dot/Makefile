CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c .subdir/A/file1.cpp -o .subdir/A/file1.o
	$(CXX) $(CFLAGS) -c .subdir/A/file2.cpp -o .subdir/A/file2.o
	$(CXX) $(CFLAGS) -c .subdir/A/file3.cpp -o .subdir/A/file3.o
	$(CXX) $(CFLAGS) -c .subdir/A/file4.cpp -o .subdir/A/file4.o
	$(CXX) $(CFLAGS) -c .subdir/A/C/file5.cpp -o .subdir/A/C/file5.o
	$(CXX) $(CFLAGS) -c .subdir/A/C/D/file6.cpp -o .subdir/A/C/D/file6.o
	$(CXX) $(CFLAGS) -c .subdir/B/main.cpp -o .subdir/B/main.o
	$(CXX) $(CFLAGS) .subdir/A/file1.o .subdir/A/file2.o .subdir/A/file3.o .subdir/A/file4.o .subdir/A/C/file5.o .subdir/A/C/D/file6.o .subdir/B/main.o -o .subdir/testcase

run: txt xml html

txt:
	./.subdir/testcase
	../../../scripts/gcovr -r . -d -o coverage.txt

xml:
	./.subdir/testcase
	../../../scripts/gcovr -r . -d -x -o coverage.xml

html:
	./.subdir/testcase
	../../../scripts/gcovr -r . -d --html --html-details -o coverage.html

clean:
	rm -f ./.subdir/testcase
	rm -f .*.gc* */*.gc* .*/*/*.gc* .*/*/*/*.gc* .*/*/*/*/*.gc*
	rm -f .*.o .*/*.o .*/*/*.o .*/*/*/*.o .*/*/*/*/*.o
	rm -f coverage.txt coverage.xml coverage*.html
