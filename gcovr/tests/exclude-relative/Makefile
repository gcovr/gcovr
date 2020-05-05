CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt xml html sonarqube

coverage.json:
	./testcase
	$(GCOVR) -e 'file1.cpp'  --json $@  # use a relative filter here

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage*.* sonarqube*.*
