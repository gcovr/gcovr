all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml

txt xml:
	./testcase
	# Create both, text and xml in one call
	$(GCOVR) -d --txt coverage.txt --cobertura-pretty --cobertura coverage.xml

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.*
