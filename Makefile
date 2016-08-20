.PHONY: install uninstall clean run check update

VENV ?= venv
BIN = $(VENV)/bin
PIP = $(BIN)/pip
FLASK = $(BIN)/flask

install:
	virtualenv $(VENV)
	$(PIP) install -U -r requirements.txt pip

uninstall:
	rm -rf $(VENV)

update: check
	$(BIN)/pip-compile -o requirements.txt requirements.in
	$(BIN)/pip-sync requirements.txt

run: check clean
	$(FLASK) run -h 0.0.0.0

clean:
	find . -name "*.pyc" -delete
	rm -rf jazzband/static/.webassets-cache
	rm -rf jazzband/static/css/styles.*.css

check:
	@test -d $(VENV) || { echo "Couldn't find venv dir. Run make install first."; exit 1; }
