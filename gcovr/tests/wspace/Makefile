all:
	cd 'src code'; $(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube coveralls

txt:
	cd 'src code'; ./testcase
	$(GCOVR) -r 'src code' -d -o coverage.txt

# generate multiple output formats together
xml html sonarqube coveralls:
	cd 'src code'; ./testcase
	$(GCOVR) -r 'src code' -d --cobertura-pretty --cobertura coverage.xml \
		--html-details coverage.html --sonarqube sonarqube.xml --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f */testcase
	rm -f */*.gc*
	rm -f coverage*.* sonarqube.xml coveralls.json
