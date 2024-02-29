CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c subdir/A/file1.cpp -o subdir/A/file1.o
	$(CXX) $(CFLAGS) -c subdir/A/File2.cpp -o subdir/A/File2.o
	$(CXX) $(CFLAGS) -c subdir/A/file3.cpp -o subdir/A/file3.o
	$(CXX) $(CFLAGS) -c subdir/A/File4.cpp -o subdir/A/File4.o
	$(CXX) $(CFLAGS) -c subdir/A/file7.cpp -o subdir/A/file7.o
	$(CXX) $(CFLAGS) -c subdir/A/C/file5.cpp -o subdir/A/C/file5.o
	$(CXX) $(CFLAGS) -c subdir/A/C/D/File6.cpp -o subdir/A/C/D/File6.o
	$(CXX) $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CFLAGS) subdir/A/file1.o subdir/A/File2.o subdir/A/file3.o subdir/A/File4.o subdir/A/C/file5.o subdir/A/C/D/File6.o subdir/A/file7.o subdir/B/main.o -o subdir/testcase

run: json lcov

coverage.json:
	./subdir/testcase
	# First exclude file pattern is for GCC, second one for clang output filenames
	$(GCOVR) -r subdir --verbose --gcov-exclude-directories '.*/A/C(?:/.*)?' --gcov-filter '.*' --gcov-exclude 'subdir#A#[Ff]ile.\.cpp\.gcov' --gcov-exclude '[Ff]ile.\.cpp##.*' --json-pretty --json $@

json: coverage.json
	echo Dummy

lcov: coverage.json
	$(GCOVR) -r subdir -a $< --lcov coverage.lcov

clean:
	rm -f ./subdir/testcase
	rm -f *.gc* */*.gc* */*/*.gc* */*/*/*.gc* */*/*/*/*.gc*
	rm -f *.o */*.o */*/*.o */*/*/*.o */*/*/*/*.o
	rm -f coverage*.*
