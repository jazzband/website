from flask import Blueprint, render_template, redirect, g, url_for, session, abort

from ..github import github
from .content import pages

account = Blueprint('account', __name__)


@account.route('/login')
def login():
    if not g.user_login:
        return github.authorize(scope=github.scope)

    if github.is_member(g.user_login):
        url = url_for('content.show', page='index')
    else:
        url = url_for('account.join')
    return redirect(url)


@account.route('/join')
def join():
    if not g.user_login:
        return redirect(url_for('account.login'))

    if github.is_member(g.user_login):
        return redirect(url_for('content.show', page='index'))

    # deny permission if there are no verified emails
    has_verified_emails = github.has_verified_emails()

    membership = None
    if has_verified_emails:
        membership = github.add_to_org(g.user_login)

    return render_template(
        'join.html',
        next_url='https://github.com/orgs/jazzband/dashboard',
        membership=membership,
        org_id=github.org_id,
        has_verified_emails=has_verified_emails,
        pages=pages,
    )


@account.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('content.show', page='index'))
