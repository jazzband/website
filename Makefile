.PHONY: install uninstall clean run check

VENV ?= venv
PIP = $(VENV)/bin/pip
MANAGE = $(VENV)/bin/python manage.py

install:
	virtualenv $(VENV)
	$(PIP) install -U -r requirements.txt pip

uninstall:
	rm -rf $(VENV)

run: check
	$(MANAGE) runserver -h 0.0.0.0

clean:
	find . -name "*.pyc" -delete

check:
	@test -d $(VENV) || { echo "Couldn't find venv dir. Run make install first."; exit 1; }
