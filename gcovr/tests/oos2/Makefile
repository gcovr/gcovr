CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	mkdir -p build
	cd build; $(CXX) $(CFLAGS) -c ../src/file1.cpp -o file1.o
	cd build; $(CXX) $(CFLAGS) -c ../src/main.cpp  -o main.o
	cd build; $(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt cobertura html sonarqube jacoco coveralls

GCOVR_TEST_OPTIONS = -r ../src .

coverage.json:
	build/testcase
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) --json-pretty --json $(abspath $@)

txt: coverage.json
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../coverage.json -o ../coverage.txt

cobertura: coverage.json
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../coverage.json --cobertura-pretty --cobertura ../cobertura.xml

html: coverage.json
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../coverage.json --html-details -o ../coverage.html

sonarqube: coverage.json
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../coverage.json --sonarqube ../sonarqube.xml

jacoco: coverage.json
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../coverage.json --jacoco ../jacoco.xml

coveralls: coverage.json
	cd build; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../coverage.json --coveralls-pretty --coveralls ../coveralls.json

clean:
	rm -f build/*
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
