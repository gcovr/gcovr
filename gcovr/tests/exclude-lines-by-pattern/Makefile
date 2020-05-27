all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json

txt:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' -o coverage.txt

xml:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' -x -o coverage.xml

html:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' --html-details -o coverage.html

sonarqube:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' --sonarqube sonarqube.xml

json:
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage.css sonarqube.xml
