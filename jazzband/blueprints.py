from .account.views import account, github_bp
from .content import content
from .members.views import members
from .projects.views import projects

blueprints = [account, content, github_bp, members, projects]


def init_app(app):
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
