# Minimal Makefile for Sphinx (apps/docs).
#
# Delegates to sphinx-build via the PATH-resolved binary in the workspace
# virtualenv. Run from this directory (apps/docs/) via one of:
#   uv run --package novelai-image-mcp-docs make html
#   sphinx-build -b html source _build/html       # if venv is active
#   pnpm docs:build                                 # via turbo
#
# i18n build layout:
#   - English (default) builds from source/ into _build/html/.
#   - Each additional language lives under source/<code>/ and builds into
#     _build/<code>/html/. All languages share the root conf.py via -c.
#   - html-all builds every language in sequence (en, zh, ja).
#   - The CI workflow (docs.yml) builds the same matrix in parallel and
#     combines the outputs into a single GitHub Pages artifact.

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = _build

.PHONY: help html livehtml linkcheck clean html-zh html-ja html-all livehtml-zh livehtml-ja

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

html:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)

livehtml:
	@sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) --open-browser

linkcheck:
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS)

# Per-language builds. Each language tree (source/zh, source/ja) is built
# independently against the shared root conf.py (-c "$(SOURCEDIR)") with a
# -D language=<code> override so Sphinx's language-aware features activate.
html-zh:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)/zh" "$(BUILDDIR)/zh/html" -c "$(SOURCEDIR)" -D language=zh $(SPHINXOPTS)

html-ja:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)/ja" "$(BUILDDIR)/ja/html" -c "$(SOURCEDIR)" -D language=ja $(SPHINXOPTS)

html-all: html html-zh html-ja
	@echo "✅ Built all languages (en, zh, ja) into $(BUILDDIR)/"

livehtml-zh:
	@sphinx-autobuild "$(SOURCEDIR)/zh" "$(BUILDDIR)/zh/html" -c "$(SOURCEDIR)" -D language=zh $(SPHINXOPTS) --open-browser

livehtml-ja:
	@sphinx-autobuild "$(SOURCEDIR)/ja" "$(BUILDDIR)/ja/html" -c "$(SOURCEDIR)" -D language=ja $(SPHINXOPTS) --open-browser

clean:
	@rm -rf "$(BUILDDIR)"
