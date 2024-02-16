# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = gcovr
SOURCEDIR     = source
BUILDDIR      = build

PYTHON ?= python

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile all clean outputs tests

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile outputs tests
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

outputs:
	gcovr -h > examples/gcovr.out

tests:
	if [ "$(GCOVR_ISOLATED_TEST)" != "zkQEVaBpXF1i" ] ; then \
		cd .. ; \
		nox -s 'docker_build_compiler(gcc-8)' ; \
		nox -s 'docker_run_compiler(gcc-8)' -- -s tests -- -k test_example ; \
	fi

