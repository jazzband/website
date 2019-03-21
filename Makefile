.PHONY: bash npm-install build clean db-migrate db-upgrade redis-cli run shell start stop update test

bash:
	docker-compose run --rm  web bash

npm-install:
	npm install

build: npm-install
	docker-compose build --pull --build-arg JAZZBAND_ENV=dev

clean: stop
	docker-compose rm -f
	find . -name "*.pyc" -delete
	rm -rf jazzband/static/.webassets-cache
	rm -rf jazzband/static/css/styles.*.css

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

update:
	docker-compose run --rm web poetry update

test: build
	docker-compose run --rm web pytest tests/
