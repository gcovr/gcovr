all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -c main.cpp -o main.o
	$(CC) -fprofile-arcs -ftest-coverage -fPIC -c update-data.c -o update-data.o
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -o testcase main.o update-data.o

run: txt xml html sonarqube coveralls

coverage.json:
	./testcase
	$(GCOVR) --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls coveralls.json

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q /S testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q *.o*
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q sonarqube.xml
	-cmd /C del /F /Q coveralls.json
else
	rm -f testcase
	rm -f *.gc*
	rm -f *.o
	rm -f coverage*.* sonarqube.xml coveralls.json
endif
