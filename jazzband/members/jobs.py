from .models import User, EmailAddress
from ..jobs import rq
from ..github import github


@rq.job
def sync_user_email_addresses(user_id):
    "Sync email addresses for user"
    user = User.query.filter_by(id=user_id).first()
    email_addresses = []
    if user and user.access_token:
        email_data = github.get_emails(access_token=user.access_token)
        for email_item in email_data:
            email_item['user_id'] = user.id
            email_addresses.append(email_item)
        EmailAddress.sync(email_addresses, key='email')
    return email_addresses
