all:
	make -C subfolder

run: html

html:
	./subfolder/subfolder/testcase
	$(GCOVR) -d --html-details -o coverage.html

clean:
	make -C subfolder clean
	rm -f coverage*.html coverage*.css
