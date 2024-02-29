CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all: copy
	$(CXX) $(CFLAGS) -c subdir/A/file1.cpp -o subdir/A/file1.o
	$(CXX) $(CFLAGS) -c subdir/A/File2.cpp -o subdir/A/File2.o
	$(CXX) $(CFLAGS) -c subdir/A/file3.cpp -o subdir/A/file3.o
	$(CXX) $(CFLAGS) -c subdir/A/File4.cpp -o subdir/A/File4.o
	$(CXX) $(CFLAGS) -c subdir/A/file7.cpp -o subdir/A/file7.o
	$(CXX) $(CFLAGS) -c subdir/A/C/file5.cpp -o subdir/A/C/file5.o
	$(CXX) $(CFLAGS) -c subdir/A/C/D/File6.cpp -o subdir/A/C/D/File6.o
	$(CXX) $(CFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CFLAGS) subdir/A/file1.o subdir/A/File2.o subdir/A/file3.o subdir/A/File4.o subdir/A/C/file5.o subdir/A/C/D/File6.o subdir/A/file7.o subdir/B/main.o -o subdir/testcase

run: html

coverage.json:
	./subdir/testcase
	$(GCOVR) -r subdir --json-pretty --json $@

html: coverage.json
	$(GCOVR) -r subdir -a $< --html-nested --sort-percentage -o coverage.html

clean:
	rm -rf ./subdir
	rm -f *.gc* */*.gc* */*/*.gc* */*/*/*.gc* */*/*/*/*.gc*
	rm -f *.o */*.o */*/*.o */*/*/*.o */*/*/*/*.o
	rm -f coverage*.*

copy:
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
	cp -fr ../nested/subdir .
else
	COPY /Y ../nested/subdir subdirs
endif
