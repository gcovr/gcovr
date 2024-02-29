CFLAGS= -fprofile-arcs -ftest-coverage -fPIC
GCOV ?= gcov

export GCOV

all:
	make -C subdir/A
	$(CXX) $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CFLAGS) subdir/B/main.o subdir/A/file1.o subdir/A/file2.o subdir/A/file3.o subdir/A/file4.o subdir/A/C/file5.o subdir/A/C/D/file6.o subdir/A/file7.o  -o subdir/B/testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	./subdir/B/testcase
	make -C subdir/A coverage
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths subdir/B/main.o
	$(GCOVR) -r subdir -g -k -o $@ --json-pretty --json -- .

txt: coverage.json
	$(GCOVR) -r subdir -a $< -o coverage.txt .

# this test also includes a separator "--"
# to ensure that nargs=? arguments can be terminated
lcov: coverage.json
	$(GCOVR) -r subdir -a $< -o coverage.lcov --lcov -- .

cobertura: coverage.json
	$(GCOVR) -r subdir -a $< -o cobertura.xml -x -- .

html: coverage.json
	$(GCOVR) -r subdir -a $< -o coverage.html --html-details --html -- .

sonarqube: coverage.json
	$(GCOVR) -r subdir -a $< -o sonarqube.xml --sonarqube -- .

jacoco: coverage.json
	$(GCOVR) -r subdir -a $< -o jacoco.xml --jacoco -- .

coveralls: coverage.json
	$(GCOVR) -r subdir -a $< -o coveralls.json --coveralls-pretty --coveralls -- .

clean:
	rm -f ./subdir/B/testcase subdir/lib.a
	rm -f *.gc* */*.gc* */*/*.gc* */*/*/*.gc* */*/*/*/*.gc*
	rm -f *.o */*.o */*/*.o */*/*/*.o */*/*/*/*.o
	rm -f coverage*.* cobertura.xml sonarqube.xml jacoco.xml coveralls.json
