
all:
	@echo "CC:   ${CC} (origin: $(origin CC))"
	@echo "CXX:  ${CXX} (origin: $(origin CXX))"
	@echo "GCOV: ${GCOV} (origin: $(origin GCOV))"
	cmake -DCMAKE_TOOLCHAIN_FILE=Toolchain.cmake -G "Ninja" -S . -B build/build
	cmake --build build/build -- -v

run: txt xml html sonarqube coveralls

coverage.json:
	cd build/build && ./gcovrtest
	$(GCOVR) --json-pretty --json coverage.json --object-directory=build/build

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
