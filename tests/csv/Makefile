include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: csv

csv:
	./testcase
	$(GCOVR) -d --csv -o coverage.csv

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.csv
