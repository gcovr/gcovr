include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt

txt:
	./testcase
	$(GCOVR) -d --txt coverage.txt --txt-report-covered

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.* cobertura.xml
