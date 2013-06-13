CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	g++ $(CFLAGS) -c subdir/A/file1.cpp -o subdir/A/file1.o
	g++ $(CFLAGS) -c subdir/A/file2.cpp -o subdir/A/file2.o
	g++ $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	g++ $(CFLAGS) subdir/A/file1.o subdir/A/file2.o subdir/B/main.o -o subdir/testcase

run: txt xml html

txt:
	./subdir/testcase
	../../../scripts/gcovr -r . -d -o coverage.txt

xml:
	./subdir/testcase
	../../../scripts/gcovr -r . -d -x -o coverage.xml

html:
	./subdir/testcase
	../../../scripts/gcovr -r . -d --html -o coverage.html

clean:
	rm -f ./subdir/testcase
	rm -f *.gc* */*.gc* */*/*.gc*
	rm -f coverage.txt coverage.xml coverage.html
