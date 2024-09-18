
all:
	$(CXX) $(CXXFLAGS) -c file5.cpp -o file5.o
	make -C D CXXFLAGS="$(CXXFLAGS)"

coverage:
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths file5.o
	make -C D coverage GCOV="$(GCOV)"
