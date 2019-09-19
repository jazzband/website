#!/usr/bin/env bash
set -eo pipefail

# then run the database migrations
flask db upgrade

exec "$@"
