CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c file5.cpp -o file5.o
	make -C D

coverage:
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths file5.o
	make -C D coverage
