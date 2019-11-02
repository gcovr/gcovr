all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -c main.cpp -o main.o
	$(CC) -fprofile-arcs -ftest-coverage -fPIC -c update-data.c -o update-data.o
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -o testcase main.o update-data.o

run: txt xml html sonarqube json

txt:
	./testcase
	$(GCOVR) -d -o coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x -o coverage.xml

html:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html

sonarqube:
	./testcase
	$(GCOVR) -d --sonarqube sonarqube.xml

json:
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f *.o
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml
