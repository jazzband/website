from flask import Blueprint, redirect, request
from sqlalchemy.sql.expression import func

from ..decorators import http_cache, templated
from .models import User

members = Blueprint('members', __name__)


@members.route('/members')
@http_cache()
@templated()
def index():
    return {
        'members': User.active_members().order_by(func.random()),
    }


@members.route('/roadies')
@http_cache()
@templated()
def roadies():
    return {
        'roadies': User.roadies().order_by(User.login),
    }


@members.route('/roadies/issue')
def roadies_issue():
    labels = request.args.get('labels', None)
    url = f'https://github.com/jazzband/roadies/issues/new'
    if labels:
        url += f'?labels={labels}'
    return redirect(url)
