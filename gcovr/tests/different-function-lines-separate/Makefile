
all:
	mkdir -p build1 build2
	cd build1 ; $(CXX) -fprofile-arcs -ftest-coverage -fPIC ../main.c -o testcase
	cd build2 ; $(CXX) -fprofile-arcs -ftest-coverage -fPIC -DFOO_OTHER_LINE ../main.c -o testcase

run: json txt xml html sonarqube coveralls

coverage.json:
	cd build1 ; ./testcase
	cd build2 ; ./testcase
	$(GCOVR) --verbose --merge-mode-functions=separate --json-pretty --json coverage.json

json: coverage.json
	# Check error with default merge mode 'strict'.
	$(GCOVR) --verbose --add-tracefile $< > coverage.log 2>&1 ; test $$? -eq 1
	cat coverage.log
	grep -E 'AssertionError: Got function .*foo.* on multiple lines: 3, 5\.' coverage.log

txt: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<   --merge-mode-functions=separate --coveralls-pretty --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $<  --merge-mode-functions=separate --sonarqube -o sonarqube.xml

clean:
	rm -rf build1 build2
	rm -f *.gc* coverage*.* sonarqube*.* coveralls.json
