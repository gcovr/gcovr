CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c foo.cpp -o foo.o
	$(CXX) $(CFLAGS) -c bar.cpp -o bar.o
	$(CXX) $(CFLAGS) -DFOO -c main.cpp -o main_foo.o
	$(CXX) $(CFLAGS) main_foo.o foo.o -o testcase_foo
	$(CXX) $(CFLAGS) -DBAR -c main.cpp -o main_bar.o
	$(CXX) $(CFLAGS) main_bar.o bar.o -o testcase_bar

run: txt xml html sonarqube json

json_foo:
	./testcase_foo
	$(GCOVR) -d --json-pretty -o coverage_foo.json

json_bar:
	./testcase_bar
	$(GCOVR) -d --json coverage_bar.json

txt: json_foo json_bar
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json -o coverage.txt

xml: json_foo json_bar
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json -x -o coverage.xml

html: json_foo json_bar
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json --html-details -o coverage.html

sonarqube: json_foo json_bar
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json --sonarqube sonarqube.xml

json: json_foo json_bar
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json --json-pretty -o coverage.json

clean:
	rm -f testcase_*
	rm -f *.gc*
	rm -f *.o
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml coverage*.json
