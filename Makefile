.PHONY: setup lint test build-demo

PYTHON ?= python3
VENV_DIR := .venv

$(VENV_DIR):
	$(PYTHON) -m venv $(VENV_DIR)

setup: $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -e ".[dev]"

lint: $(VENV_DIR)
	$(VENV_DIR)/bin/ruff check src tests

test: $(VENV_DIR)
	$(VENV_DIR)/bin/pytest -q

build-demo: $(VENV_DIR)
	$(VENV_DIR)/bin/pharmassist-catalog-fr build-demo --raw-dir data/raw --out products.demo.json
