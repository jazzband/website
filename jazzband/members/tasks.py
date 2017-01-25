from celery import shared_task
from . import commands


@shared_task(soft_time_limit=10)
def sync_user_email_addresses(user_id):
    commands.sync_user_email_addresses(user_id)
