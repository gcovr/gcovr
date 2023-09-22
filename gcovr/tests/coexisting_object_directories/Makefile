
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
	$(GCOVR) --json-pretty --json $@ --object-directory=build/$*  build/$*

coverage.json: coverage.a.json coverage.b.json coverage.c.json
	#make coverage.a.json & make coverage.b.json & make coverage.c.json & wait

coverage.%.txt: coverage.json
	$(GCOVR) -a coverage.$*.json -o $@

txt: coverage.a.txt coverage.b.txt coverage.c.txt

cobertura.%.xml: coverage.json
	$(GCOVR) -a coverage.$*.json --cobertura-pretty --cobertura $@

cobertura: cobertura.a.xml cobertura.b.xml cobertura.c.xml

coverage.%.html: coverage.json
	$(GCOVR) -a coverage.$*.json --html-details -o $@

html: coverage.a.html coverage.b.html coverage.c.html

coveralls.%.json: coverage.json
	$(GCOVR) -a coverage.$*.json --coveralls-pretty --coveralls $@

coveralls: coveralls.a.json coveralls.b.json coveralls.c.json

sonarqube.%.xml: coverage.json
		$(GCOVR) -a coverage.$*.json --sonarqube -o $@

sonarqube: sonarqube.a.xml sonarqube.b.xml sonarqube.c.xml

clean:
	rm -rf build
	rm -f coverage.*.* cobertura.*.* sonarqube.*.* coveralls.*.json
