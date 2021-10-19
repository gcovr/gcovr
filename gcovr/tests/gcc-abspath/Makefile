all:
	cd subfolder&& $(MAKE)

run: html

html:
	cd subfolder&& ./testcase
	mv -f --target-directory . subfolder/*.gc??
	$(GCOVR) -d --html-details -o coverage.html

clean:
	cd subfolder&& make clean
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html
