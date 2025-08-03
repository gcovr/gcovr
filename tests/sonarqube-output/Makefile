include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: sonarqube

sonarqube:
	./testcase
	$(GCOVR) --sonarqube=sonarqube-line.xml --sonarqube-metric=line
	$(GCOVR) --sonarqube=sonarqube-branch.xml --sonarqube-metric=branch
	$(GCOVR) --sonarqube=sonarqube-condition.xml --sonarqube-metric=condition
	$(GCOVR) --sonarqube=sonarqube-decision.xml --sonarqube-metric=decision --decisions

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f sonarqube*.*
