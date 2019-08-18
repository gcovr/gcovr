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

run: txt xml html sonarqube json

txt:
	cd build && ./gcovrtest
	$(GCOVR) -d -o coverage.txt

xml:
	cd build && ./gcovrtest
	$(GCOVR) -d -x -o coverage.xml

html:
	cd build && ./gcovrtest
	$(GCOVR) -d --html-details -o coverage.html

sonarqube:
	cd build && ./gcovrtest
	$(GCOVR) -d --sonarqube sonarqube.xml

json:
	# pass

clean:
	rm -rf build
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml

