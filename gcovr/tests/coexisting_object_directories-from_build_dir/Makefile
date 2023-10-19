
build.%:
	mkdir -p build/$* && cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build/$* -D ODD=$(ODD)
	cmake --build build/$* -- -v

all:
	@echo "CC:   ${CC} (origin: $(origin CC))"
	@echo "CXX:  ${CXX} (origin: $(origin CXX))"
	@echo "GCOV: ${GCOV} (origin: $(origin GCOV))"
	make build.a ODD=ON
	make build.b ODD=OFF
	make build.c ODD=ON

run: txt cobertura html sonarqube coveralls

execute:
	cd build/a && ./parallel_call
	cd build/b && ./parallel_call
	cd build/c && ./parallel_call

coverage.%.json:
	$(eval base_dir := $(shell pwd))
	$(eval build_dir := $(base_dir)/build/$*)
	cd $(build_dir) && $(GCOVR) --json-pretty --json $(base_dir)/$@ --object-directory=$(build_dir) --root $(base_dir) $(build_dir)

coverage.json: execute
	make coverage.a.json & make coverage.b.json & make coverage.c.json & wait

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
