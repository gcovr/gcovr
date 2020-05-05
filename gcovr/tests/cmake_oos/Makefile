# Original build.sh script from ticket:
#   rm -fr build
#   mkdir build
#   cd build
#   cmake ..
#   make
#   gcovrtest

CMAKE ?= cmake

all:
	mkdir -p build
	cd build && $(CMAKE) .. && make

run: txt xml html sonarqube

coverage.json:
	cd build && ./gcovrtest
	$(GCOVR) --json coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

clean:
	rm -rf build
	rm -f coverage*.* sonarqube*.*
