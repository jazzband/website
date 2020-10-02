from flask import Blueprint, redirect
from sqlalchemy.sql.expression import func

from ..decorators import templated
from .models import User

members = Blueprint("members", __name__)


@members.route("/members")
@templated()
def index():
    return {"members": User.active_members().order_by(func.random())}


@members.route("/roadies")
@templated()
def roadies():
    return {"roadies": User.roadies().order_by(User.login)}


@members.route("/roadies/issue")
def roadies_issue():
    url = "https://github.com/jazzband-roadies/help/issues/new/choose"
    return redirect(url)


@members.route("/website/issue")
def website_issue():
    url = "https://github.com/jazzband-roadies/website/issues/new"
    return redirect(url)
