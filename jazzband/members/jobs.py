from ..jobs import rq
from ..github import github

from .models import EmailAddress, User


@rq.job
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
