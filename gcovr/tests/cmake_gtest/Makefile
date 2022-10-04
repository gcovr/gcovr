
all:
	@echo "CC:   ${CC} (origin: $(origin CC))"
	@echo "CXX:  ${CXX} (origin: $(origin CXX))"
	@echo "GCOV: ${GCOV} (origin: $(origin GCOV))"
	cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build
	cmake --build build -- -v

run: txt xml html sonarqube coveralls

coverage.json:
	cd build && ./gcovr_gtest
	$(GCOVR) --filter source/ --json-pretty --json coverage.json --object-directory=build

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<  --coveralls-pretty --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

clean:
	rm -rf build
	rm -f coverage*.* sonarqube*.* coveralls.json
