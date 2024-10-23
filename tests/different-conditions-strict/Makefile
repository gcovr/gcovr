include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir -p build1 build2
	cd build1 ; cat ../main_hdr.c ../main1.c ../main_ftr.c > ../main.c ; $(CC) $(CXXFLAGS) ../main.c -o testcase
	cd build2 ; cat ../main_hdr.c ../main2.c ../main_ftr.c > ../main.c ; $(CC) $(CXXFLAGS) ../main.c -o testcase

run: json

json:
	cd build1 ; ./testcase
	cd build2 ; ./testcase
	$(GCOVR) --verbose --merge-mode-conditions=strict --json-pretty --json > coverage.log 2>&1 ; test $$? -eq 64 | cat coverage.log
	cat coverage.log
	touch empty
	grep -E 'The number of conditions must be equal.*main\.c:4' coverage.log

clean:
	rm -rf build1 build2
	rm -f *.gc* coverage*.* main.c empty
