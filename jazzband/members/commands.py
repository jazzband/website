import click
from flask.cli import with_appcontext

from ..db import postgres
from ..github import github
from . import jobs
from .models import User


@click.command('members')
@with_appcontext
def sync_members():
    "Syncs members"
    members_data = github.get_members()
    User.sync(members_data)

    stored_ids = set(user.id for user in User.query.all())
    fetched_ids = set(m['id'] for m in members_data)
    stale_ids = stored_ids - fetched_ids
    if stale_ids:
        User.query.filter(
            User.id.in_(stale_ids)
        ).update({'is_member': False}, 'fetch')
        postgres.session.commit()


@click.command('emails')
@click.option('--user_id', '-u', default=None)
@with_appcontext
def sync_email_addresses(user_id):
    "Sync email addresses for user"
    return jobs.sync_email_addresses(user_id)
