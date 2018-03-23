# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = gcovr
SOURCEDIR     = source
BUILDDIR      = build

PYTHON ?= python
SCREENSHOT_FROM_HTML = wkhtmltoimage --width 700 --quality 5
SCREENSHOTS = images/screenshot-html.png images/screenshot-html-details.example.cpp.png

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile all outputs clean tests clean-images

# keep the screenshots
.PRECIOUS: $(SCREENSHOTS)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile $(SCREENSHOTS) outputs
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

images/screenshot-%.png: examples/example-%.html
	$(SCREENSHOT_FROM_HTML) $< $@

examples/example-%.html:
	cd examples; ./example_html.sh

outputs:
	gcovr -h > examples/gcovr.out

tests:
	$(PYTHON) -m pytest examples -v

clean-images:
	rm -f $(SCREENSHOTS)
