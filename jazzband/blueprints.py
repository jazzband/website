from .account.views import account
from .content import content
from .members.views import members
from .projects.views import projects

blueprints = [
    account,
    content,
    members,
    projects,
]


def init_app(app):
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
