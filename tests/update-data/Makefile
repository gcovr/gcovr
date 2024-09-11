include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) -c main.cpp -o main.o
	$(CC) $(CFLAGS) -c update-data.c -o update-data.o
	$(CXX) $(CXXFLAGS) -o testcase main.o update-data.o

run: txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f *.o
	rm -f coverage*.* cobertura.xml sonarqube.xml jacoco.xml coveralls.json
