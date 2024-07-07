# Original build.sh script from ticket:
#   rm -fr build
#   mkdir build
#   cd build
#   cmake ..
#   make
#   testcase

BASE_OS:=$(shell uname | cut -d'-' -f1)
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
  CMAKE_GENERATOR := "Unix Makefiles"
else
  CMAKE_GENERATOR := "MSYS Makefiles"
endif

all:
	@echo "CC:   ${CC} (origin: $(origin CC))"
	@echo "CXX:  ${CXX} (origin: $(origin CXX))"
	@echo "GCOV: ${GCOV} (origin: $(origin GCOV))"
	mkdir -p build
	cd build && cmake -G $(CMAKE_GENERATOR) -DCMAKE_BUILD_TYPE=PROFILE .. && make

run: txt cobertura html sonarqube jacoco coveralls

coverage.json:
	cd build && ./testcase
	$(GCOVR) --json-pretty --json coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<  --coveralls-pretty --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco -o jacoco.xml

clean:
	rm -rf build
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
