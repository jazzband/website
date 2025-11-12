import sys

import click
from flask.cli import with_appcontext

from .db import postgres, redis
from .members.commands import sync_email_addresses, sync_members
from .projects.commands import (
    add_repo_to_members_team,
    send_new_upload_notifications,
    setup_project_leads_team,
    sync_project_members,
    sync_project_team,
    sync_projects,
    update_all_projects_members_team,
)


@click.command("db")
@with_appcontext
def check_db():
    "Checks database connection"
    try:
        postgres.session.execute("SELECT 1;")
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        sys.exit(1)


@click.command("redis")
@with_appcontext
def check_redis():
    "Checks database connection"
    try:
        response = redis.ping()
    except Exception:
        response = None
    if not response:
        print("Redis ping failed.")
        sys.exit(1)


def init_app(app):
    @app.cli.group()
    def sync():
        "Sync Jazzband data."

    @app.cli.group()
    def send():
        "Send notifications."

    @app.cli.group()
    def check():
        "Checks some backends."

    check.add_command(check_db)
    check.add_command(check_redis)

    send.add_command(send_new_upload_notifications)

    sync.add_command(sync_members)
    sync.add_command(sync_projects)
    sync.add_command(sync_project_members)
    sync.add_command(sync_project_team)
    sync.add_command(sync_email_addresses)
    sync.add_command(setup_project_leads_team)
    sync.add_command(add_repo_to_members_team)
    sync.add_command(update_all_projects_members_team)
