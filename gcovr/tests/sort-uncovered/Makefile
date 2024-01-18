CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c file2.cpp -o file2.o
	$(CXX) $(CFLAGS) -c file3.cpp -o file3.o
	$(CXX) $(CFLAGS) -c file4.cpp -o file4.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o file2.o file3.o file4.o -o testcase

run: txt html

GCOVR_TEST_OPTIONS = --sort uncovered-number

coverage.json:
	./testcase
	$(GCOVR) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< -o coverage.txt

html: coverage.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage*.* cobertura*.* sonarqube*.*
