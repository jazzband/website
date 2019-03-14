FROM node as npm

COPY package.json package-lock.json /tmp/

WORKDIR /tmp

RUN npm install

# -----------------------------------------------------------------------------

FROM python:3.6-stretch

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LANG=C.UTF-8
ENV PYTHONPATH=/app/
ENV PATH=/app/.local/bin:$PATH

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

COPY requirements.txt /tmp/

RUN set -x \
    && pip install -r /tmp/requirements.txt

COPY . /app/

COPY --from=npm /tmp/node_modules /app/node_modules/

RUN chown -R 10001:10001 /app

USER 10001

WORKDIR /app

ENTRYPOINT ["/app/docker-entrypoint.sh", "--"]
