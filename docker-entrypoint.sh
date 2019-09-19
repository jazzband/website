#!/usr/bin/env bash
set -eo pipefail

# default variables
: "${PORT:=5000}"

# then run the database migrations
flask db upgrade

exec "$@"
