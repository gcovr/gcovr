all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt cobertura

txt cobertura:
	./testcase
	# Create both, text and cobertura in one call
	$(GCOVR) -d --txt coverage.txt --cobertura-pretty --cobertura cobertura.xml

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.*
