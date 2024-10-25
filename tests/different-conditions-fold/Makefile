include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir -p build1 build2
	cd build1 ; cat ../main_hdr.c ../main1.c ../main_ftr.c > ../main.c ; $(CC) $(CXXFLAGS) ../main.c -o testcase
	cd build2 ; cat ../main_hdr.c ../main2.c ../main_ftr.c > ../main.c ; $(CC) $(CXXFLAGS) ../main.c -o testcase

run: json txt lcov cobertura html sonarqube coveralls

	cd build1 ; ./testcase
	cd build2 ; ./testcase
	$(GCOVR) --verbose --merge-mode-conditions=fold --json-pretty --json coverage.json

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
	rm -rf build1 build2
	rm -f *.gc* coverage*.* cobertura*.* sonarqube*.* coveralls.json main.c
