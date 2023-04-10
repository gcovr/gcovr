all:
	@echo "This test uses a tracefile."

run: html

html:
	$(GCOVR) -d --json-add-tracefile input.json --html-details coverage.html; test $$? -eq 128

clean:
	rm -f coverage*.html coverage.css
