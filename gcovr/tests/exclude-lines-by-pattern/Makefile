all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt cobertura html sonarqube coveralls

txt:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' -o coverage.txt

cobertura:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' --cobertura-pretty --cobertura cobertura.xml

html:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' --html-details -o coverage.html

sonarqube:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' --sonarqube sonarqube.xml

coveralls:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage*.html coverage.css cobertura.xml sonarqube.xml coveralls.json
