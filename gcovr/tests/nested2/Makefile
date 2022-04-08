CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	make -C subdir/A
	$(CXX) $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CFLAGS) subdir/B/main.o subdir/A/file1.o subdir/A/file2.o subdir/A/file3.o subdir/A/file4.o subdir/A/C/file5.o subdir/A/C/D/file6.o subdir/A/file7.o  -o subdir/B/testcase

run: txt xml html sonarqube coveralls

coverage.json:
	./subdir/B/testcase
	$(GCOVR) -r subdir --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -r subdir -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -r subdir -a $< --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -r subdir -a $< --html-details --html-theme blue -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -r subdir -a $< --sonarqube sonarqube.xml

coveralls:coverage.json
	$(GCOVR) -r subdir -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f ./subdir/B/testcase subdir/lib.a
	rm -f *.gc* */*.gc* */*/*.gc* */*/*/*.gc* */*/*/*/*.gc*
	rm -f *.o */*.o */*/*.o */*/*/*.o */*/*/*/*.o
	rm -f coverage*.* sonarqube*.* coveralls.json
