all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -c main.cpp -o main.o
	$(CC) -fprofile-arcs -ftest-coverage -fPIC -c update-data.c -o update-data.o
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -o testcase main.o update-data.o

run: txt xml html sonarqube coveralls

coverage.json:
	./testcase
	$(GCOVR) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f *.o
	rm -f coverage*.* sonarqube.xml coveralls.json
