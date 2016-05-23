from flask_login import current_user


def current_user_is_roadie():
    if not current_user.is_authenticated:
        return False
    return bool(current_user.is_roadie)
