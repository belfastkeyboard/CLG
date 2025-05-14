#!/bin/sh
.ONESHELL:
.DEFAULT_GOAL := run

VENV_NAME := gaeilge_venv
VENV_PATH := $(CURDIR)/$(VENV_NAME)

# Check if the virtual environment already exists
VENV_EXISTS := $(wildcard $(VENV_PATH))

clean:
	rm -rf $(VENV_PATH)

setup_venv:
ifndef VENV_EXISTS
		python3 -m venv $(VENV_PATH)
else
		@echo "Virtual Environment $(VENV_PATH) already exists"
endif

install_requirements: setup_venv
	$(VENV_PATH)/bin/python -m ensurepip --upgrade
	$(VENV_PATH)/bin/pip install -r $(CURDIR)/requirements.txt


run: install_requirements
	$(VENV_PATH)/bin/python $(CURDIR)/main.py