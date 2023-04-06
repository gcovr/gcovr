
all:
	@echo "CC:   ${CC} (origin: $(origin CC))"
	@echo "CXX:  ${CXX} (origin: $(origin CXX))"
	@echo "GCOV: ${GCOV} (origin: $(origin GCOV))"
	mkdir -p build/a && cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build/a -D ODD=ON
	mkdir -p build/b && cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build/b -D ODD=OFF
	mkdir -p build/c && cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build/c -D ODD=ON
	cmake --build build/a -- -v
	cmake --build build/b -- -v
	cmake --build build/c -- -v

run: txt cobertura html sonarqube coveralls

coverage.%.json:
	cd build/$* && ./parallel_call
	$(GCOVR) --json-pretty --json $@ --object-directory=build/$*

coverage.json: coverage.a.json coverage.b.json coverage.c.json
	#make coverage.a.json & make coverage.b.json & make coverage.c.json & wait

coverage.%.txt:
	$(GCOVR) -a coverage.$*.json -o $@

txt: coverage.json coverage.a.txt coverage.b.txt coverage.c.txt
	$(GCOVR) -a coverage.a.json -o coverage.a.txt

cobertura: coverage.json
	$(GCOVR) -a coverage.a.json --cobertura-pretty --cobertura cobertura.a.xml

html: coverage.json
	$(GCOVR) -a coverage.a.json --html-details -o coverage.a.html

coveralls: coverage.json
	$(GCOVR) -a coverage.a.json --coveralls-pretty --coveralls coveralls.a.json

sonarqube: coverage.json
	$(GCOVR) -a coverage.a.json --sonarqube -o sonarqube.a.xml

clean:
	rm -rf build
	rm -f coverage.*.* cobertura.*.* sonarqube.*.* coveralls.*.json
