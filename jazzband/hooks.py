import json
import uuid

from flask_hookserver import Hooks

from .db import redis
from .members.models import User
from .projects.tasks import update_project_by_hook
from .tasks import spinach


hooks = Hooks()


@hooks.hook("ping")
def ping(data, guid):
    return "pong"


@hooks.hook("membership")
def membership(data, guid):
    if data["scope"] != "team":
        return
    member = User.query.filter_by(id=data["member"]["id"]).first()
    if member is None:
        return
    if data["action"] == "added":
        member.is_member = True
        member.save()
    elif data["action"] == "removed":
        member.is_member = False
        member.save()
    return "Thanks"


@hooks.hook("member")
def member(data, guid):
    # only if the action is to add a member and if there is repo data
    if data.get("action") == "added" and "repository" in data:
        hook_id = f"repo-added-{uuid.uuid4()}"
        redis.setex(
            hook_id, 60 * 5, json.dumps(data)  # expire the hook hash in 5 minutes
        )
        spinach.schedule(update_project_by_hook, hook_id)
        return hook_id
    return "Thanks"
