
build.%:
	mkdir -p build/$* && cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build/$* -D ODD=$(if $(filter b,$*),OFF,ON)
	cmake --build build/$* -- -v

all: build.a build.b build.c

run: txt cobertura html sonarqube coveralls

coverage.%.json:
	$(eval base_dir := $(shell pwd))
	$(eval build_dir := $(base_dir)/build/$*)
	cd $(build_dir) && ./parallel_call
	$(GCOVR) --json-pretty --json $(base_dir)/$@ $(build_dir)

coverage.%.txt: coverage.%.json
	$(GCOVR) -a coverage.$*.json -o $@

txt: coverage.a.txt coverage.b.txt coverage.c.txt

cobertura.%.xml: coverage.%.json
	$(GCOVR) -a coverage.$*.json --cobertura-pretty --cobertura $@

cobertura: cobertura.a.xml cobertura.b.xml cobertura.c.xml

coverage.%.html: coverage.%.json
	$(GCOVR) -a coverage.$*.json --html-details -o $@

html: coverage.a.html coverage.b.html coverage.c.html

coveralls.%.json: coverage.%.json
	$(GCOVR) -a coverage.$*.json --coveralls-pretty --coveralls $@

coveralls: coveralls.a.json coveralls.b.json coveralls.c.json

sonarqube.%.xml: coverage.%.json
		$(GCOVR) -a coverage.$*.json --sonarqube -o $@

sonarqube: sonarqube.a.xml sonarqube.b.xml sonarqube.c.xml

clean:
	rm -rf build
	rm -f coverage.*.* cobertura.*.* sonarqube.*.* coveralls.*.*
