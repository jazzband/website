.PHONY: bash npm-build npm-install build clean db-migrate db-upgrade redis-cli run shell start stop update test pytest image envvar ci cert trust

bash:
	docker-compose run --rm  web bash

npm-install:
	npm install

npm-build:
	npm run build

image:
	docker-compose build --pull

build: npm-install npm-build image

clean: stop
	docker-compose rm -f
	find . -name "*.pyc" -delete
	rm -rf jazzband/static/dist

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
	docker-compose run --rm web pip install -r requirements.txt

pytest:
	docker-compose run --rm web pytest tests/

test: pytest

envvar:
	cp .env-dist .env

ci: envvar test

trust:
	@command -v mkcert || (echo "mkcert command not found. Please install first, see https://github.com/FiloSottile/mkcert" && exit 1)
	mkcert -install

cert: trust
	cd certs && mkcert jazzband.local "*.jazzband.local" jazzband.local localhost 127.0.0.1 ::1 && cd ..
