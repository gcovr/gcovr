CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

GCOVR += --verbose

all:
	$(CXX) $(CFLAGS) -c subdir/A/file1.cpp -o subdir/A/file1.o
	$(CXX) $(CFLAGS) -c subdir/A/file2.cpp -o subdir/A/file2.o
	$(CXX) $(CFLAGS) -c subdir/A/file3.cpp -o subdir/A/file3.o
	$(CXX) $(CFLAGS) -c subdir/A/file4.cpp -o subdir/A/file4.o
	$(CXX) $(CFLAGS) -c subdir/A/file7.cpp -o subdir/A/file7.o
	$(CXX) $(CFLAGS) -c subdir/A/C/file5.cpp -o subdir/A/C/file5.o
	$(CXX) $(CFLAGS) -c subdir/A/C/D/file6.cpp -o subdir/A/C/D/file6.o
	$(CXX) $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CFLAGS) subdir/A/file1.o subdir/A/file2.o subdir/A/file3.o subdir/A/file4.o subdir/A/C/file5.o subdir/A/C/D/file6.o subdir/A/file7.o subdir/B/main.o -o subdir/testcase

run: txt xml html sonarqube coveralls

# Activate verbose mode because of hanging pypy in GitHub actions
coverage.json:
	./subdir/testcase
	$(GCOVR) -j 4 -r subdir --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -r subdir -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -r subdir --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -a $< -r subdir --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< -r subdir --sonarqube sonarqube.xml

coveralls:coverage.json
	$(GCOVR) -a $< -r subdir --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f ./subdir/testcase
	rm -f *.gc* */*.gc* */*/*.gc* */*/*/*.gc* */*/*/*/*.gc*
	rm -f *.o */*.o */*/*.o */*/*/*.o */*/*/*/*.o
	rm -f coverage*.* sonarqube*.* coveralls.json
