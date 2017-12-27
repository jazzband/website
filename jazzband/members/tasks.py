from celery import shared_task

from .models import User, EmailAddress
from ..github import github


@shared_task(soft_time_limit=10)
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
