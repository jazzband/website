import click
from flask.cli import with_appcontext

from ..github import github
from .models import db, User, EmailAddress


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
        db.session.commit()


@click.command('emails')
@click.argument('user_id', metavar='<user_id>')
@with_appcontext
def sync_user_email_addresses(user_id):
    "Sync email addresses for user"
    user = User.query.filter_by(id=user_id).first()
    email_addresses = []
    if user.access_token:
        email_data = github.get_emails(access_token=user.access_token)
        for email_item in email_data:
            email_item['user_id'] = user.id
            email_addresses.append(email_item)
        EmailAddress.sync(email_addresses, key='email')
    return email_addresses
