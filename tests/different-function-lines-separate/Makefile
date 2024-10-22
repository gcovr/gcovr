include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir -p build1 build2
	cd build1 ; $(CXX) $(CXXFLAGS) ../main.c -o testcase
	cd build2 ; $(CXX) $(CXXFLAGS) -DFOO_OTHER_LINE ../main.c -o testcase

run: json txt lcov cobertura html sonarqube coveralls

coverage.json:
	cd build1 ; ./testcase
	cd build2 ; ./testcase
	$(GCOVR) --verbose --merge-mode-functions=separate --json-pretty --json coverage.json

json: coverage.json
	# Check error with default merge mode 'strict'.
	$(GCOVR) --verbose --json-add-tracefile $< > coverage.log 2>&1 ; test $$? -eq 64 | cat coverage.log
	cat coverage.log
	grep -E 'Got function .*foo.* in .*different-function-lines-separate.func\.h on multiple lines: 3, 5\.' coverage.log

txt: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<   --merge-mode-functions=separate --coveralls-pretty --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate --sonarqube -o sonarqube.xml

clean:
	rm -rf build1 build2
	rm -f *.gc* coverage*.* cobertura*.* sonarqube*.* coveralls.json
