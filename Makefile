.PHONY: bash build clean compile db-migrate db-upgrade redis-cli run shell start stop sync

bash:
	docker-compose run web bash

build:
	docker-compose build --pull

clean: stop
	docker-compose rm -f
	find . -name "*.pyc" -delete
	rm -rf jazzband/static/.webassets-cache
	rm -rf jazzband/static/css/styles.*.css

compile:
	docker-compose run web pip-compile -U -o requirements.txt requirements.in

db-migrate:
	docker-compose run web flask db migrate

db-upgrade:
	docker-compose run web flask db upgrade

redis-cli:
	docker-compose run redis redis-cli -h redis

run:
	docker-compose up

shell:
	docker-compose run web flask shell

start:
	docker-compose up -d

stop:
	docker-compose stop

sync: compile
	docker-compose run web pip-sync requirements.txt
