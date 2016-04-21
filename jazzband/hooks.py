from flask.ext.hookserver import Hooks

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
    return "Thanks"
