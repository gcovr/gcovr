# Original build.sh script from ticket:
#   rm -fr build
#   mkdir build
#   cd build
#   cmake ..
#   make
#   gcovrtest

CMAKE ?= cmake

all:
ifeq ($(OS),Windows_NT)
	-mkdir build
	cd build && $(CMAKE) -G "MinGW Makefiles" .. && make
else
	mkdir -p build
	cd build && $(CMAKE) .. && make
endif

run: txt xml html sonarqube coveralls

coverage.json:
ifeq ($(OS),Windows_NT)
	cd build && .\gcovrtest
else
	cd build && ./gcovrtest
endif
	$(GCOVR) --json coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<  --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q /S build
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q sonarqube*.*
	-cmd /C del /F /Q coveralls.json
else
	rm -rf build
	rm -f coverage*.* sonarqube*.* coveralls.json
endif
