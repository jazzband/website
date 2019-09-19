FROM node as npm

COPY . /tmp/

WORKDIR /tmp

RUN npm install \
    && npm run build

# -----------------------------------------------------------------------------

FROM python:3.7

ENV PYTHONPATH=/app/ \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    LANG=C.UTF-8 \
    PORT=5000

# add a non-privileged user for installing and running the application
# don't use --create-home option to prevent populating with skeleton files
RUN mkdir /app && \
    chown 10001:10001 /app && \
    groupadd --gid 10001 app && \
    useradd --no-create-home --uid 10001 --gid 10001 --home-dir /app app

RUN set -x \
    && apt-get update \
    && apt-get install locales -y \
    && locale-gen en_US.UTF-8

# install a few essentials and clean apt caches afterwards
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential curl git libpq-dev \
        postgresql-client gettext sqlite3 libffi-dev \
        inotify-tools wget bzip2 wait-for-it && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install -U pip

WORKDIR /app
COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app/

COPY --from=npm /tmp/node_modules /app/node_modules/
COPY --from=npm /tmp/jazzband/static/dist /app/jazzband/static/dist/

RUN chown -R 10001:10001 /app

USER 10001

EXPOSE 5000

ENTRYPOINT ["/app/docker-entrypoint.sh", "--"]
