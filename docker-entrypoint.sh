#!/usr/bin/env bash
set -eo pipefail

# default variables
: "${PORT:=5000}"
: "${TIMEOUT:=60}"

# first wait for the database
wait-for-it redis:6379 -t ${TIMEOUT}
wait-for-it db:5432 -t ${TIMEOUT}

# then run the database migrations
flask db upgrade

# then build the assets
flask assets build

exec "$@"
