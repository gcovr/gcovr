all:
	make -C subfolder

run: txt xml html sonarqube json

txt:
	./subfolder/testcase
	$(GCOVR) -d -o coverage.txt

xml:
	./subfolder/testcase
	$(GCOVR) -d -x -o coverage.xml

html:
	./subfolder/testcase
	$(GCOVR) -d --html-details -o coverage.html

sonarqube:
	./subfolder/testcase
	$(GCOVR) -d --sonarqube sonarqube.xml

json:
	# pass

clean:
	make -C subfolder clean
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml
