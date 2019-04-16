from flask_login import LoginManager

from ..members.models import User

login_manager = LoginManager()
login_manager.login_view = "github.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
