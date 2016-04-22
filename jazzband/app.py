import os
from flask import Flask, render_template, send_from_directory


def create_app(config_path):
    # setup flask
    app = Flask('jazzband')

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

    # load decoupled config variables
    app.config.from_object(config_path)

    from .models import db, User, Project, EmailAddress
    db.init_app(app)

    from flask_migrate import Migrate
    Migrate(app, db)

    from .admin import admin, JazzbandModelView
    admin.init_app(app)
    admin.add_view(JazzbandModelView(User, db.session))
    admin.add_view(JazzbandModelView(Project, db.session))
    admin.add_view(JazzbandModelView(EmailAddress, db.session))

    if 'OPBEAT_SECRET_TOKEN' in os.environ:
        from opbeat.contrib.flask import Opbeat
        Opbeat(app, logging=True)

    if not app.debug:
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    from whitenoise import WhiteNoise
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=app.static_folder,
        prefix=app.static_url_path,
    )

    # setup github-flask
    from .github import github
    github.init_app(app)

    from .hooks import hooks
    hooks.init_app(app)

    # setup webassets
    from .assets import assets
    assets.init_app(app)

    # setup session store
    from flask.ext.session import Session
    Session(app)

    from flask.ext.compress import Compress
    Compress(app)

    from .content import about_pages, news_pages, content
    about_pages.init_app(app)
    news_pages.init_app(app)
    app.register_blueprint(content)

    from .account import account, login_manager
    app.register_blueprint(account)
    login_manager.init_app(app)

    from .members import members
    app.register_blueprint(members)

    from .projects import projects
    app.register_blueprint(projects)

    @app.context_processor
    def app_context_processor():
        return {
            'about': about_pages,
            'news': news_pages,
            'User': User,
            'Project': Project,
        }

    return app
