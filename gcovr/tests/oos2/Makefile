CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	mkdir -p build
	cd build; $(CXX) $(CFLAGS) -c ../src/file1.cpp -o file1.o
	cd build; $(CXX) $(CFLAGS) -c ../src/main.cpp  -o main.o
	cd build; $(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt xml html sonarqube

GCOVR_TEST_OPTIONS = -r ../src .

txt:
	build/testcase
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -d -o ../coverage.txt

xml:
	build/testcase
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -d -x -o ../coverage.xml

html:
	build/testcase
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -d --html-details -o ../coverage.html

sonarqube:
	build/testcase
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -d --sonarqube ../sonarqube.xml

clean:
	rm -f build/*
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml
