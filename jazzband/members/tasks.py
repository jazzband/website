import logging
from datetime import timedelta

from spinach import Tasks

from ..account import github
from ..config import ONE_MINUTE
from ..db import postgres, redis
from .models import EmailAddress, User

logger = logging.getLogger(__name__)

tasks = Tasks()


@tasks.task(name="sync_members", periodicity=timedelta(minutes=30), max_retries=3)
def sync_members():
    # use a lock to make sure we don't run this multiple times
    with redis.lock("sync_members", ttl=ONE_MINUTE * 14):
        members_data = github.get_members()
        User.sync(members_data)

        stored_ids = {user.id for user in User.query.all()}
        fetched_ids = {m["id"] for m in members_data}
        stale_ids = stored_ids - fetched_ids
        if stale_ids:
            User.query.filter(User.id.in_(stale_ids)).update(
                {"is_member": False}, "fetch"
            )
            postgres.session.commit()


@tasks.task(name="sync_email_addresses", max_retries=5)
def sync_email_addresses(user_id):
    "Sync email addresses for user"
    # load user or raise an exception if not found
    user = User.query.filter(User.id == user_id).one()

    if not user.access_token:
        raise ValueError(f"No access token for user {user.login}")

    logger.info(
        "Updating emails for user %s with access token %s..",
        user_id,
        user.access_token[:6],
    )

    email_addresses = []

    for email_item in github.get_emails(user):
        email_item["user_id"] = user.id
        email_addresses.append(email_item)

    EmailAddress.sync(email_addresses, key="email")

    return email_addresses
