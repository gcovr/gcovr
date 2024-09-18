include $(dir $(MAKEFILE_LIST))../common.mk

all:
	cd 'src code'; $(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

# generate multiple output formats together
txt lcov cobertura html sonarqube jacoco coveralls:
	cd 'src code'; ./testcase
	$(GCOVR) -r 'src code' -d --txt coverage.txt --lcov coverage.lcov --cobertura-pretty --cobertura cobertura.xml \
		--html-details coverage.html --sonarqube sonarqube.xml --jacoco-pretty --jacoco jacoco.xml --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f */testcase
	rm -f */*.gc*
	rm -f coverage*.* cobertura.xml sonarqube.xml jacoco.xml coveralls.json
