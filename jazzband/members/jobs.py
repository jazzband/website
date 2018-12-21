from ..jobs import rq

from . import commands


@rq.job
def sync_email_addresses(user_id):
    "Sync email addresses for user"
    return commands.sync_email_addresses(user_id)
