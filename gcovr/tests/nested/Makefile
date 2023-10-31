CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c subdir/A/file1.cpp -o subdir/A/file1.o
	$(CXX) $(CFLAGS) -c subdir/A/File2.cpp -o subdir/A/File2.o
	$(CXX) $(CFLAGS) -c subdir/A/file3.cpp -o subdir/A/file3.o
	$(CXX) $(CFLAGS) -c subdir/A/File4.cpp -o subdir/A/File4.o
	$(CXX) $(CFLAGS) -c subdir/A/file7.cpp -o subdir/A/file7.o
	$(CXX) $(CFLAGS) -c subdir/A/C/file5.cpp -o subdir/A/C/file5.o
	$(CXX) $(CFLAGS) -c subdir/A/C/D/File6.cpp -o subdir/A/C/D/File6.o
	$(CXX) $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CFLAGS) subdir/A/file1.o subdir/A/File2.o subdir/A/file3.o subdir/A/File4.o subdir/A/C/file5.o subdir/A/C/D/File6.o subdir/A/file7.o subdir/B/main.o -o subdir/testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	./subdir/testcase
	$(GCOVR) -r subdir --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -r subdir -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -r subdir -a $< --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -r subdir -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -r subdir -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -r subdir -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -r subdir -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -r subdir -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f ./subdir/testcase
	rm -f *.gc* */*.gc* */*/*.gc* */*/*/*.gc* */*/*/*/*.gc*
	rm -f *.o */*.o */*/*.o */*/*/*.o */*/*/*/*.o
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
