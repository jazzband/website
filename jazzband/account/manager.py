from flask_login import LoginManager, current_user

from ..github import github
from ..members.models import User

login_manager = LoginManager()
login_manager.login_view = "account.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@github.access_token_getter
def token_getter():
    if current_user.is_authenticated:
        return current_user.access_token
