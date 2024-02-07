all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt

txt:
	./testcase
	$(GCOVR) -d --output coverage.txt

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt
