CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

BASE_OS:=$(shell uname | cut -d'-' -f1)

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

run: txt cobertura html sonarqube coveralls

coverage.json:
	./subdir/testcase
	$(GCOVR) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
	rm -Rf subdir
else
	if [ -d "subdir" ]; then\
		cmd.exe /C "rmdir /S /Q subdir";\
	fi
endif
	rm -f coverage*.* cobertura*.* sonarqube*.* coveralls.json

links:
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
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
	ln -s . loop;
else
	if [ -d "subdir" ]; then\
		cmd.exe /C "rmdir /S /Q subdir";\
	fi
	mkdir subdir;
	cmd.exe /C "cd subdir && mklink /j B ..\..\nested\subdir\B"
	cmd.exe /C "cd subdir && mkdir m"
	cmd.exe /C "cd subdir\m && mklink /j n ..\..\..\nested\subdir\A"
	cmd.exe /C "cd subdir && mklink /j A m\n"
	cmd.exe /C "cd subdir && mklink /j loop ."
endif
	find ../nested -name '*.o' -or -name '*.gc*' -delete || exit 0
