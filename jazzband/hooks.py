from datetime import datetime
import hmac
import json
import uuid

from flask import current_app
import werkzeug.security

from .db import redis
from .hookserver import Hooks
from .members.models import User
from .projects.tasks import update_project_by_hook
from .tasks import spinach


hooks = Hooks()


def safe_str_cmp(a: str, b: str) -> bool:
    """This function compares strings in somewhat constant time. This
    requires that the length of at least one string is known in advance.

    Returns `True` if the two strings are equal, or `False` if they are not.
    """

    if isinstance(a, str):
        a = a.encode("utf-8")  # type: ignore

    if isinstance(b, str):
        b = b.encode("utf-8")  # type: ignore

    return hmac.compare_digest(a, b)


# Monkeypatch hookserver to fix werkzeug compatibility.
werkzeug.security.safe_str_cmp = safe_str_cmp


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
