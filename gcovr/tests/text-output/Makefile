all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml

txt xml:
	./testcase
ifneq ($(OS),Windows_NT)
	# Create both, text and xml in one call
endif
	$(GCOVR) -d --txt coverage.txt --xml coverage.xml

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q coverage.*
else
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.*
endif
