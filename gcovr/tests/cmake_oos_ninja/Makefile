
all:
	@echo "CC:   ${CC} (origin: $(origin CC))"
	@echo "CXX:  ${CXX} (origin: $(origin CXX))"
	@echo "GCOV: ${GCOV} (origin: $(origin GCOV))"
	cp -f ../cmake_oos/main.cpp ./
	cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build
	cmake --build build -- -v

run: txt cobertura html sonarqube coveralls

coverage.json:
	cd build && ./gcovrtest
	$(GCOVR) --json-pretty --json coverage.json --object-directory=build

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

clean:
	rm -rf build main.cpp
	rm -f coverage*.* cobertura*.* sonarqube*.* coveralls.json
