import json
import uuid
from datetime import datetime

from flask import current_app
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
        return "Scope wasn't team."

    member_id = data["member"]["id"]
    member = User.query.filter_by(id=member_id).first()
    if member is None:
        return f"No member found with id {member_id}."

    # only remove the user if they are member of the main members team
    # not if they are removed from project teams
    if data["team"]["slug"] != current_app.config["GITHUB_MEMBERS_TEAM_SLUG"]:
        return "User not a Members team member."

    if data["action"] == "added":
        member.is_member = True
        member.save()
        return "User {member} is a member now."
    elif data["action"] == "removed":
        member.left_at = datetime.utcnow()
        member.is_member = False
        member.save()
        return "User {member} is not a member anymore."
    else:
        return "Thanks."


@hooks.hook("repository")
def repository(data, guid):
    # only if the action is to add a member and if there is repo data
    if data.get("action") in ("transferred", "created") and "repository" in data:
        hook_id = f"repo-added-{uuid.uuid4()}"
        redis.setex(
            # expire the hook hash in 5 minutes
            hook_id,
            60 * 5,
            json.dumps(data),
        )
        spinach.schedule(update_project_by_hook, hook_id)
        return f"Started updating the project using hook id {hook_id}."
    else:
        return "No action needed."
