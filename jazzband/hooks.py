from flask import render_template
from flask_hookserver import Hooks

from .github import github
from .db import postgres
from .members.models import User


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
        postgres.session.commit()
    elif data['action'] == 'removed':
        member.is_member = False
        postgres.session.commit()
    return 'Thanks'


@hooks.hook('member')
def member(data, guid):
    # if no action was given or it was about removing a member
    if data.get('action') != 'added':
        return 'Thanks'

    # if there is no repo data
    repo = data.get('repository')
    if repo is None:
        return 'Thanks'

    # get list of roadies and set them as the default assignees
    roadies = User.query.filter_by(
        is_member=True,
        is_banned=False,
        is_roadie=True,
    )
    assignees = [roadie.login for roadie in roadies]
    # add sender of the hook as well if given
    if 'sender' in data:
        assignees.append(data['sender']['login'])

    issue_title = render_template('hooks/project-title.txt', **data)
    issue_body = render_template('hooks/project-body.txt', **data)

    issues = github.get(
        'repos/jazzband/roadies/issues',
        access_token=github.admin_access_token,
    )
    # if there is already an issue with that title, escape
    if issue_title in [issue['title'] for issue in issues]:
        return

    data = {
        'title': issue_title,
        'body': issue_body,
        'labels': ['guidelines', 'review'],
        'assignees': assignees,
    }

    # create a new issue
    github.post(
        'repos/jazzband/roadies/issues',
        data,
        access_token=github.admin_access_token,
    )
    return 'Thanks'
