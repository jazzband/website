from urlparse import urlparse
from flask import (Blueprint, render_template, redirect, g, url_for, session,
                   request, current_app, flash)

from ..github import github

account = Blueprint('account', __name__)


@account.route('/callback')
@github.authorized_handler
def callback(access_token):
    next_url = url_for('account.join')

    if access_token is None:
        session.clear()
        return redirect(next_url)

    session['user_access_token'] = access_token
    return redirect(next_url)


@github.access_token_getter
def token_getter():
    return g.user_access_token


@account.route('/login')
def login():
    if not g.user_login:
        return github.authorize(scope=github.scope)

    if github.is_member(g.user_login):
        url = url_for('content.show', page='index')
    else:
        url = url_for('account.join')
    return redirect(url)


def good_referrer():
    """
    In case no referrer is given return False immediatedly.
    Otherwise this will look in the HOSTNAMES setting
    """
    if not request.referrer:
        return False
    parsed_referrer = urlparse(request.referrer)
    return parsed_referrer.netloc in current_app.config['HOSTNAMES']


@account.route('/join')
def join():
    if not good_referrer():
        flash("Do you really want to join?")
        return redirect(url_for('content.show', page='index'))

    if not g.user_login:
        return redirect(url_for('account.login'))

    if github.is_member(g.user_login):
        flash("You've already joined Jazzband")
        return redirect(url_for('content.show', page='index'))

    is_banned = github.is_banned(g.user_login)

    # deny permission if there are no verified emails
    has_verified_emails = github.has_verified_emails()

    membership = None
    if has_verified_emails:
        membership = github.add_to_org(g.user_login)
        if membership:
            flash("Jazzband has asked GitHub to send you an invitation")

    return render_template(
        'join.html',
        next_url='https://github.com/orgs/jazzband/dashboard',
        membership=membership,
        org_id=github.org_id,
        has_verified_emails=has_verified_emails,
        is_banned=is_banned,
    )


@account.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('content.show', page='index'))
