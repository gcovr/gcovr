all:
	make -C subfolder

run: html

html:
	./subfolder/subfolder/testcase
	$(GCOVR) -d --html-details -o coverage.html; test $$? -eq 7

clean:
	make -C subfolder clean
	rm -f coverage*.html
