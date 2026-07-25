# Minimal Makefile for Sphinx (apps/docs).
#
# Delegates to sphinx-build via the PATH-resolved binary in the workspace
# virtualenv. Run from this directory (apps/docs/) via one of:
#   uv run --package novelai-image-mcp-docs make html
#   sphinx-build -b html source _build/html       # if venv is active
#   pnpm docs:build                                 # via turbo

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = _build

.PHONY: help html livehtml linkcheck clean

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

html:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)

livehtml:
	@sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) --open-browser

linkcheck:
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS)

clean:
	@rm -rf "$(BUILDDIR)"
