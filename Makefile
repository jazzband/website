.PHONY: bash npm-install build clean compile db-migrate db-upgrade redis-cli run shell start stop sync test

bash:
	docker-compose run --rm  web bash

npm-install:
	npm install

build: npm-install
	docker-compose build --pull

clean: stop
	docker-compose rm -f
	find . -name "*.pyc" -delete
	rm -rf jazzband/static/.webassets-cache
	rm -rf jazzband/static/css/styles.*.css

compile:
	docker-compose run --rm web pip-compile -U -o requirements.txt requirements.in

db-migrate:
	docker-compose run --rm web flask db migrate

db-upgrade:
	docker-compose run --rm web flask db upgrade

redis-cli:
	docker-compose run --rm redis redis-cli -h redis

run:
	docker-compose up

shell:
	docker-compose run --rm web flask shell

start:
	docker-compose up -d

stop:
	docker-compose stop

sync: compile
	docker-compose run --rm web pip-sync requirements.txt

test: npm-install
	docker-compose run --rm web pip install --user -r tests/requirements.txt
	docker-compose run --rm web pytest tests/
