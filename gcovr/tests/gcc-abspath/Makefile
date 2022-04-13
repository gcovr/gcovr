all:
	cd subfolder&& $(MAKE)

run: json

json:
	cd subfolder&& ./testcase
	mv -f --target-directory . subfolder/*.gc??
	$(GCOVR) -d --json-pretty --json coverage.json

clean:
	cd subfolder&& make clean
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.json
