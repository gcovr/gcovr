include $(dir $(MAKEFILE_LIST))../common.mk

all:
	python3 ../create_gz.py conditions-2.json conditions-2.gcov.json.gz
	python3 ../create_gz.py conditions-4.json conditions-4.gcov.json.gz

run: json txt lcov cobertura html sonarqube coveralls

coverage.json:
	$(GCOVR) --gcov-use-existing --verbose --merge-mode-conditions=fold --json-pretty --json coverage.json

json: coverage.json

txt: coverage.json
	$(GCOVR) -a $<  -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $<  --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -a $<  --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $<  --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<   --coveralls-pretty --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $<  --sonarqube -o sonarqube.xml

clean:
	rm -f *.gcov.json.gz coverage*.* cobertura*.* sonarqube*.* coveralls.json
