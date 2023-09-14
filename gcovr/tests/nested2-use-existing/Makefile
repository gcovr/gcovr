CFLAGS= -fprofile-arcs -ftest-coverage -fPIC
GCOV ?= gcov

export GCOV

all:
	make -C subdir/A
	$(CXX) $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CFLAGS) subdir/B/main.o subdir/A/file1.o subdir/A/file2.o subdir/A/file3.o subdir/A/file4.o subdir/A/C/file5.o subdir/A/C/D/file6.o subdir/A/file7.o  -o subdir/B/testcase

run: txt cobertura html sonarqube jacoco coveralls

# this test also includes a separator "--"
# to ensure that nargs=? arguments can be terminated
coverage.json:
	./subdir/B/testcase
	make -C subdir/A coverage
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths subdir/B/main.o
	$(GCOVR) -r subdir -g -k -o $@ --json-pretty --json -- .

txt: coverage.json
	$(GCOVR) -r subdir -a $< -o coverage.txt .

cobertura: coverage.json
	$(GCOVR) -r subdir -a $< -o cobertura.xml -x -- .

html: coverage.json
	$(GCOVR) -r subdir -a $< --html-details -o coverage.html .

sonarqube: coverage.json
	$(GCOVR) -r subdir -a $< --sonarqube sonarqube.xml .

jacoco: coverage.json
	$(GCOVR) -r subdir -a $< --jacoco jacoco.xml .

coveralls: coverage.json
	$(GCOVR) -r subdir -a $< --coveralls-pretty --coveralls coveralls.json .

clean:
	rm -f ./subdir/B/testcase subdir/lib.a
	rm -f *.gc* */*.gc* */*/*.gc* */*/*/*.gc* */*/*/*/*.gc*
	rm -f *.o */*.o */*/*.o */*/*/*.o */*/*/*/*.o
	rm -f coverage*.* cobertura.xml sonarqube.xml jacoco.xml coveralls.json
