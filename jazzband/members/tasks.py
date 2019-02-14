from datetime import timedelta

from spinach import Tasks

from ..db import postgres, redis
from ..github import github
from .models import EmailAddress, User

tasks = Tasks()


@tasks.task(name='sync_members', periodicity=timedelta(seconds=60))
def sync_members():
    # use a lock to make sure we don't run this multiple times
    with redis.lock("sync_members", ttl=60 * 1000):

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


@tasks.task(name='sync_email_addresses', max_retries=5)
def sync_email_addresses(user_id=None):
    "Sync email addresses for user"
    if user_id is None:
        users = User.query.all()
    else:
        users = User.query.filter_by(id=user_id)

    for user in users:
        email_addresses = []
        if user.access_token:
            email_data = github.get_emails(access_token=user.access_token)
            for email_item in email_data:
                email_item['user_id'] = user.id
                email_addresses.append(email_item)
            EmailAddress.sync(email_addresses, key='email')

    return email_addresses
