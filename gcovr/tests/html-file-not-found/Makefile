all:
	@echo "This test uses a tracefile."

run: html

html:
	$(GCOVR) -d --add-tracefile input.json --html-details coverage.html; test $$? -eq 7

clean:
	rm -f coverage*.html coverage.css
