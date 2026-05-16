.PHONY: install install-dev demo test lint clean help

PY := python3
VENV := .venv
ACTIVATE := . $(VENV)/bin/activate

help:
	@echo "Targets:"
	@echo "  install      runtime deps (offline placeholder backend works immediately)"
	@echo "  install-dev  add pytest + Gemini backend"
	@echo "  demo         render 3 branded placeholder infographics into output/"
	@echo "  test         run unit + e2e tests"
	@echo "  lint         ruff check"
	@echo "  clean        wipe venv, caches, output/"

$(VENV):
	$(PY) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip --quiet

install: $(VENV)
	$(ACTIVATE) && pip install -r requirements.txt --quiet

install-dev: $(VENV)
	$(ACTIVATE) && pip install -r requirements-dev.txt --quiet

demo: install
	$(ACTIVATE) && $(PY) -m src.demo

test: install-dev
	$(ACTIVATE) && $(PY) -m pytest -q

lint: install-dev
	$(ACTIVATE) && pip install ruff --quiet && ruff check src tests

clean:
	rm -rf $(VENV) .pytest_cache output
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
