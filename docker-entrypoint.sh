#!/usr/bin/env bash
set -eo pipefail

# default variables
: "${PORT:=5000}"
: "${SLEEP:=1}"
: "${TRIES:=60}"

function wait_for_check {(
  tries=0
  echo "Waiting for $1 to respond..."
  while true; do
    [[ $tries -lt $TRIES ]] || return
    flask check $1 >/dev/null 2>&1
    [[ $? -eq 0 ]] && return
    sleep $SLEEP
    tries=$((tries + 1))
  done
)}

# first wait for the database
wait_for_check redis & wait_for_check postgres

# then run the database migrations
flask db upgrade

# then build the assets
flask assets build

exec "$@"
