import sys

import click
from flask.cli import with_appcontext

from .models import db, redis
from .members.commands import sync_members
from .projects.commands import sync_projects


@click.command('db')
@with_appcontext
def check_db():
    "Checks database connection"
    try:
        db.session.execute('SELECT 1;')
    except Exception as exc:
        print(f'Database connection failed: {exc}')
        sys.exit(1)


@click.command('redis')
@with_appcontext
def check_redis():
    "Checks database connection"
    try:
        response = redis.ping()
    except Exception:
        response = None
    if not response:
        print('Redis ping failed.')
        sys.exit(1)


def init_app(app):

    @app.cli.group()
    def sync():
        "Sync Jazzband data"

    @app.cli.group()
    def check():
        "Checks some backends"

    check.add_command(check_db)
    check.add_command(check_redis)

    sync.add_command(sync_members)
    sync.add_command(sync_projects)
