from flask import Blueprint

from .decorators import templated
from .models import User

members = Blueprint('members', __name__)


@members.route('/members')
@templated()
def index():
    members = User.query.filter_by(
        is_member=True,
        is_banned=False,
    ).filter(
        User.login != 'jazzband-bot'
    ).order_by(
        User.login
    )
    return {
        'members': members,
    }


@members.route('/roadies')
@templated()
def roadies():
    roadies = User.query.filter_by(
        is_member=True,
        is_banned=False,
        is_roadie=True,
    ).order_by(
        User.login
    )
    return {
        'roadies': roadies,
    }
