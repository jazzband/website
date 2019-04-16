from flask import current_app
from flask.globals import LocalProxy


def github_blueprint():
    return current_app.blueprints["github"]


github = LocalProxy(github_blueprint)
