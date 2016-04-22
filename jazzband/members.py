from flask import Blueprint

from .decorators import http_cache, templated
from .models import User

members = Blueprint('members', __name__)


@members.route('/members')
@http_cache()
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
@http_cache()
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
