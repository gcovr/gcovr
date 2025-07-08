
build.%:
	mkdir -p build/$* && cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S . -B build/$* -D ODD=$(if $(filter b,$*),OFF,ON)
	cmake --build build/$* -- -v

all: build.a build.b build.c

run: txt cobertura html sonarqube coveralls

# .NOTPARALLEL with targets needs at least gnumake 4.4.
# We get sporadic raise conditions on windows runner with 4.2.
# Let's configure it manual
# .NOTPARALLEL: coverage.a.json coverage.b.json coverage.c.json
coverage.c.json : | coverage.b.json
coverage.b.json : | coverage.a.json

coverage.%.json:
	cd build/$* && ./parallel_call
	$(GCOVR) --verbose --json-pretty --json $@ --object-directory=build/$*

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
