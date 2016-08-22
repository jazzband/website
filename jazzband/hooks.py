from flask import render_template
from flask_hookserver import Hooks

from .github import github
from .models import db, User


hooks = Hooks()


@hooks.hook('ping')
def ping(data, guid):
    return 'pong'


@hooks.hook('membership')
def membership(data, guid):
    if data['scope'] != 'team':
        return
    member = User.query.filter_by(id=data['member']['id']).first()
    if member is None:
        return
    if data['action'] == 'added':
        member.is_member = True
        db.session.commit()
    elif data['action'] == 'removed':
        member.is_member = False
        db.session.commit()
    return 'Thanks'


@hooks.hook('member')
def member(data, guid):
    # if no action was given or it was about removing a member
    if data.get('action') != 'added':
        return

    # if there is no repo data
    repo = data.get('repository')
    if repo is None:
        return

    data = {
        'title': render_template('hooks/transfer-title.txt', **data),
        'body': render_template('hooks/transfer-body.txt', **data),
        'labels': ['transfer'],
    }

    return github.post(
        'repos/jazzband/roadies/issues',
        data,
        access_token=github.admin_access_token,
    )
