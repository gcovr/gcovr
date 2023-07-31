CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

BASE_OS:=$(shell uname | cut -d'-' -f1)

all: links
	cd symlink; $(CXX) $(CFLAGS) main.cpp -o testcase

run: txt

txt:
	cd symlink; ./testcase
	cd symlink; $(GCOVR) --txt ../coverage.txt --root $${PWD}

links:
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
	if [ -d "symlink" ]; then\
		rm -Rf symlink;\
	fi
	ln -s ./root symlink;
else
	cmd.exe /C setup.cmd
endif
	find ./root -name '*.o' -or -name '*.gc*' -delete || exit 0

clean:
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
	rm -Rf symlink
else
	if [ -d "symlink" ]; then\
		cmd.exe /C "rmdir /S /Q symlink";\
	fi
endif
	rm -f root/*.gc* root/coverage*.* root/cobertura*.* sonarqube*.* root/coveralls.json root/out.log
