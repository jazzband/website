import os
from flask import Flask, render_template, send_from_directory

from flask_compress import Compress
from flask_migrate import Migrate
from flask_session import Session
from werkzeug.contrib.fixers import ProxyFix
from whitenoise import WhiteNoise

from . import commands
from .account import account, login_manager
from .admin import admin, JazzbandModelView
from .assets import assets
from .content import about_pages, news_pages, content
from .github import github
from .hooks import hooks
from .members import members
from .models import db, User, Project, EmailAddress
from .projects import projects


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


@app.route('/favicon.ico')
def favicon():
    filename = 'favicon.ico'
    cache_timeout = app.get_send_file_max_age(filename)
    return send_from_directory(os.path.join(app.static_folder, 'favicons'),
                               filename,
                               mimetype='image/vnd.microsoft.icon',
                               cache_timeout=cache_timeout)


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
    response.headers['Jazzband'] = "We're all part of the band"
    return response


@app.cli.group()
def sync():
    "Sync Jazzband data"
sync.command()(commands.projects)
sync.command()(commands.members)


db.init_app(app)

Migrate(app, db)

admin.init_app(app)
admin.add_view(JazzbandModelView(User, db.session))
admin.add_view(JazzbandModelView(Project, db.session))
admin.add_view(JazzbandModelView(EmailAddress, db.session))

if 'OPBEAT_SECRET_TOKEN' in os.environ:
    from opbeat.contrib.flask import Opbeat
    Opbeat(app, logging=True)

if 'HEROKU_APP_NAME' in os.environ:
    app.wsgi_app = ProxyFix(app.wsgi_app)

app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root=app.static_folder,
    prefix=app.static_url_path,
)

# setup github-flask
github.init_app(app)

hooks.init_app(app)

# setup webassets
assets.init_app(app)

# setup session store
Session(app)

Compress(app)

about_pages.init_app(app)
news_pages.init_app(app)
app.register_blueprint(content)

app.register_blueprint(account)
login_manager.init_app(app)

app.register_blueprint(members)

app.register_blueprint(projects)
