CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all: links
	$(CXX) $(CFLAGS) -c subdir/A/file1.cpp -o subdir/A/file1.o
	$(CXX) $(CFLAGS) -c subdir/A/file2.cpp -o subdir/A/file2.o
	$(CXX) $(CFLAGS) -c subdir/A/file3.cpp -o subdir/A/file3.o
	$(CXX) $(CFLAGS) -c subdir/A/file4.cpp -o subdir/A/file4.o
	$(CXX) $(CFLAGS) -c subdir/A/file7.cpp -o subdir/A/file7.o
	$(CXX) $(CFLAGS) -c subdir/A/C/file5.cpp -o subdir/A/C/file5.o
	$(CXX) $(CFLAGS) -c subdir/m/n/C/D/file6.cpp -o subdir/m/n/C/D/file6.o
	$(CXX) $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CFLAGS) subdir/A/file1.o subdir/A/file2.o subdir/A/file3.o subdir/A/file4.o subdir/A/C/file5.o subdir/m/n/C/D/file6.o subdir/A/file7.o subdir/B/main.o -o subdir/testcase

run: txt xml html sonarqube coveralls

coverage.json:
	./subdir/testcase
	$(GCOVR) --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls coveralls.json

clean:
	rm -Rf subdir
	rm -f coverage*.* sonarqube*.* coveralls.json

links:
	if [ -d "subdir" ]; then\
		rm -Rf subdir;\
	fi
	mkdir subdir;\
	cd subdir;\
	ln -s ../../nested/subdir/B .;\
	mkdir -p m;\
	cd m;\
	ln -s ../../../nested/subdir/A n;\
	cd ..;\
	ln -s m/n A;\
	ln -s . loop;\
	cd ..;
	find ../nested -name '*.o' -or -name '*.gc*' -delete || exit 0
