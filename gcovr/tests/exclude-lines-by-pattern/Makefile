all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube coveralls

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

coveralls:
	./testcase
	$(GCOVR) -d --exclude-lines-by-pattern ' *panic\([^)]*\);' --coveralls coveralls.json

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q coverage.txt
	-cmd /C del /F /Q coverage.xml
	-cmd /C del /F /Q coverage.html
	-cmd /C del /F /Q coverage.css
	-cmd /C del /F /Q sonarqube.xml
	-cmd /C del /F /Q coveralls.json
else
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage.css sonarqube.xml coveralls.json
endif
