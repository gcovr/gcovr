all:
ifeq ($(OS),Windows_NT)
	cd "src code" && $(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase
else
	cd 'src code'; $(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase
endif

run: txt xml html sonarqube coveralls

txt:
ifeq ($(OS),Windows_NT)
	cd "src code" && .\testcase
else
	cd 'src code'; ./testcase
endif
	$(GCOVR) -r 'src code' -d -o coverage.txt

# generate multiple output formats together
xml html sonarqube coveralls:
ifeq ($(OS),Windows_NT)
	cd "src code" && .\testcase
	$(GCOVR) -r "src code" -d -x -o coverage.xml \
		--html-details coverage.html --sonarqube sonarqube.xml --coveralls coveralls.json
else
	cd 'src code'; ./testcase
	$(GCOVR) -r 'src code' -d -x -o coverage.xml \
		--html-details coverage.html --sonarqube sonarqube.xml --coveralls coveralls.json
endif

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q "src code\testcase*"
	-cmd /C del /F /Q "src code\*.gc*"
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q coveralls.json
else
	rm -f */testcase
	rm -f */*.gc*
	rm -f coverage*.* sonarqube.xml coveralls.json
endif
