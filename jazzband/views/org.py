from flask import abort, Blueprint, redirect, g, session, url_for

from ..github import github

org = Blueprint('org', __name__)


@github.access_token_getter
def token_getter():
    return g.user_access_token


@org.route('/callback')
@github.authorized_handler
def callback(access_token):
    next_url = url_for('account.join')

    if access_token is None:
        session.clear()
        return redirect(next_url)

    session['user_access_token'] = access_token
    return redirect(next_url)
