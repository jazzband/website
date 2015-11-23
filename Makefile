.PHONY: install uninstall clean run

VENV ?= venv
PIP = $(VENV)/bin/pip
MANAGE = $(ENV)/bin/python manage.py

install:
	virtualenv $(VENV)
	$(PIP) install -U -r requirements.txt pip

uninstall:
	rm -rf $(VENV)

run:
	$(MANAGE) runserver -h 0.0.0.0

clean:
	find . -name "*.pyc" -delete
