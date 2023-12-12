
build.%:
	mkdir -p build/$* && cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build/$* -D ODD=$(if $(filter b,$*),OFF,ON)
	cmake --build build/$* -- -v

all: build.a build.b build.c

run: txt cobertura html sonarqube coveralls

.NOTPARALLEL: coverage.a.json coverage.b.json coverage.c.json

coverage.%.json:
	$(eval base_dir := $(shell pwd))
	$(eval build_dir := $(base_dir)/build/$*)
	cd $(build_dir) && ./parallel_call
	cd $(build_dir) && GCOV_STRIP=99 GCOV_PREFIX=$(build_dir) $(GCOVR) --json-pretty --json $(base_dir)/$@ --object-directory=$(build_dir) --root $(base_dir)

coverage.%.txt: coverage.%.json
	$(GCOVR) -a $< -o $@

txt: coverage.a.txt coverage.b.txt coverage.c.txt

cobertura.%.xml: coverage.%.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura $@

cobertura: cobertura.a.xml cobertura.b.xml cobertura.c.xml

coverage.%.html: coverage.%.json
	$(GCOVR) -a $< --html-details -o $@

html: coverage.a.html coverage.b.html coverage.c.html

coveralls.%.json: coverage.%.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls $@

coveralls: coveralls.a.json coveralls.b.json coveralls.c.json

sonarqube.%.xml: coverage.%.json
		$(GCOVR) -a $< --sonarqube -o $@

sonarqube: sonarqube.a.xml sonarqube.b.xml sonarqube.c.xml

clean:
	rm -rf build
	rm -f run.*.done
	rm -f coverage.*.* cobertura.*.* sonarqube.*.* coveralls.*.*
