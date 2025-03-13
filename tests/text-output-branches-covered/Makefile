include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt

txt:
	./testcase
	$(GCOVR) -d --txt-metric branch --txt-report-covered --txt coverage.txt

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.*
