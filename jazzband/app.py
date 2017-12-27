from flask import Flask, render_template

from flask_compress import Compress
from flask_migrate import Migrate
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore
from werkzeug.contrib.fixers import ProxyFix
from whitenoise import WhiteNoise
from . import admin, cli
from .account import account, login_manager
from .assets import assets
from .celery import celery_ext
from .content import about_pages, news_pages, content
from .errors import sentry
from .github import github
from .headers import talisman
from .hooks import hooks
from .email import mail
from .models import db, redis
from .members.views import members
from .members.models import User
from .projects.models import Project
from .projects.views import projects


# setup flask
app = Flask('jazzband')
# load decoupled config variables
app.config.from_object('jazzband.config')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template('forbidden.html'), 403


@app.errorhandler(500)
def error(error):
    return render_template('error.html'), 500


@app.context_processor
def app_context_processor():
    return {
        'about': about_pages,
        'news': news_pages,
        'User': User,
        'Project': Project,
    }


@app.after_request
def add_vary_header(response):
    response.vary.add('Cookie')
    response.headers['Jazzband'] = "We're all part of this."
    return response


talisman.init_app(
    app,
    force_https=app.config['IS_PRODUCTION'],
    force_file_save=True,
    content_security_policy=app.config['CSP_RULES'],
    content_security_policy_report_only=app.config['CSP_REPORT_ONLY'],
    content_security_policy_report_uri=app.config['CSP_REPORT_URI'],
)

db.init_app(app)

migrate = Migrate(app, db)

redis.init_app(app)

sentry.init_app(app)

celery_ext.init_app(app)
celery = celery_ext.celery

admin.init_app(app)

cli.init_app(app)

if app.config['IS_PRODUCTION']:
    app.wsgi_app = ProxyFix(app.wsgi_app)

app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root=app.static_folder,
    prefix=app.static_url_path,
)

mail.init_app(app)

# setup github-flask
github.init_app(app)

hooks.init_app(app)

# setup webassets
assets.init_app(app)

# setup session store
session_store = RedisStore(redis)
KVSessionExtension(session_store, app)

Compress(app)

about_pages.init_app(app)
news_pages.init_app(app)
app.register_blueprint(content)

app.register_blueprint(account)
login_manager.init_app(app)

app.register_blueprint(members)

app.register_blueprint(projects)
