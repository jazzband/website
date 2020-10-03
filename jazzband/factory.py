from flask import Flask
from flask_compress import Compress
from flask_kvsession import KVSessionExtension
from flask_migrate import Migrate
from simplekv.memory.redisstore import RedisStore
from werkzeug.middleware.proxy_fix import ProxyFix
from whitenoise import WhiteNoise

from . import admin, cli, errors, logging  # noqa
from .account.manager import login_manager
from .cache import cache
from .content import about_pages, news_pages
from .db import postgres, redis
from .email import mail
from .headers import talisman
from .hooks import hooks
from .members.models import User
from .projects.models import Project
from .tasks import spinach


def create_app():
    # setup flask
    app = Flask("jazzband")
    # load decoupled config variables
    app.config.from_object("jazzband.config")

    @app.context_processor
    def app_context_processor():
        return {
            "about": about_pages,
            "news": news_pages,
            "User": User,
            "Project": Project,
            "config": app.config,
        }

    @app.after_request
    def add_vary_header(response):
        response.vary.add("Cookie")
        response.headers["Jazzband"] = "We are all part of this."
        return response

    talisman.init_app(
        app,
        force_https=app.config["IS_PRODUCTION"],
        force_file_save=True,
        content_security_policy=app.config["CSP_RULES"],
        content_security_policy_report_only=app.config["CSP_REPORT_ONLY"],
        content_security_policy_report_uri=app.config["CSP_REPORT_URI"],
        feature_policy=app.config["FEATURE_POLICY"],
    )

    postgres.init_app(app)

    redis.init_app(app)

    Migrate(app, postgres)

    cache.init_app(app)

    admin.init_app(app)

    cli.init_app(app)

    spinach.init_app(app)

    errors.init_app(app)

    if app.config["IS_PRODUCTION"]:
        app.wsgi_app = ProxyFix(app.wsgi_app)
        app.wsgi_app = WhiteNoise(app.wsgi_app, root="static/")

    mail.init_app(app)

    hooks.init_app(app)

    # setup session store
    session_store = RedisStore(redis)
    KVSessionExtension(session_store, app)

    Compress(app)

    about_pages.init_app(app)
    news_pages.init_app(app)

    login_manager.init_app(app)

    from . import blueprints  # noqa

    blueprints.init_app(app)

    return app
