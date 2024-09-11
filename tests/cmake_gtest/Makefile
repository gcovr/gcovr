include $(dir $(MAKEFILE_LIST))../common.mk

all:
	@echo "CC:   ${CC} (origin: $(origin CC))"
	@echo "CXX:  ${CXX} (origin: $(origin CXX))"
	@echo "GCOV: ${GCOV} (origin: $(origin GCOV))"
	cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build
	cmake --build build -- -v

run: txt cobertura html sonarqube jacoco coveralls

coverage.json:
	cd build && ./gcovr_gtest
	$(GCOVR) --filter source/ --json-pretty --json coverage.json --gcov-object-directory=build

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
