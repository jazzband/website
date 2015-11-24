from decouple import config
from flask import (Flask, g, session, redirect, url_for, abort,
                   render_template)
from flask.ext.assets import Environment as Assets, Bundle
from flask.ext.github import GitHub, GitHubError
from flask.ext.session import Session
from flask_flatpages import FlatPages
import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.wikilinks import WikiLinkExtension
import redis
from whitenoise import WhiteNoise


def smart_pygmented_markdown(text, flatpages=None, page=None):
    """
    Render Markdown text to HTML, similarly to Flask-Flatpages'
    renderer, except we store the markdown instance on the page.
    """
    extensions = flatpages.config('markdown_extensions') if flatpages else []
    if not extensions:
        extensions = ['codehilite']
    md = markdown.Markdown(extensions)
    page.md = md
    page.pages = flatpages
    return md.convert(text)


SECRET_KEY = config('SECRET_KEY', 'dev key')
DEBUG = config('DEBUG', True, cast=bool)

FLATPAGES_ROOT = 'docs'
FLATPAGES_EXTENSION = ['.md']
FLATPAGES_MARKDOWN_EXTENSIONS = [
    'codehilite',
    'fenced_code',
    'footnotes',
    'admonition',
    'tables',
    'abbr',
    'smarty',
    WikiLinkExtension(base_url='/docs/', end_url='', html_class=''),
    TocExtension(permalink=True),
]
FLATPAGES_HTML_RENDERER = smart_pygmented_markdown

# Set these values in the .env file or env vars
GITHUB_CLIENT_ID = config('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = config('GITHUB_CLIENT_SECRET', '')
GITHUB_ORG_ID = config('GITHUB_ORG_ID', 'jazzband')
GITHUB_SCOPE = config('GITHUB_SCOPE', 'read:org,user:email')
GITHUB_MEMBERS_TEAM_ID = config('GITHUB_MEMBERS_TEAM_ID', 0, cast=int)
GITHUB_ROADIES_TEAM_ID = config('GITHUB_ROADIES_TEAM_ID', 0, cast=int)
GITHUB_ADMIN_TOKEN = config('GITHUB_ADMIN_TOKEN', '')

VALIDATE_IP = False

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = 'jazzhands'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_USE_SIGNER = config('SESSION_USE_SIGNER', True, cast=bool)
SESSION_REDIS = redis.from_url(config('REDIS_URL', 'redis://127.0.0.1:6379/0'))
PERMANENT_SESSION_LIFETIME = 60 * 60
DATAURI_MAX_SIZE = 1024 * 1024

# setup flask
app = Flask(__name__)
app.config['LIBSASS_STYLE'] = 'compressed'

# load decoupled config variables
app.config.from_object(__name__)

app.wsgi_app = WhiteNoise(app.wsgi_app,
                          root=app.static_folder,
                          prefix=app.static_url_path)

# setup github-flask
github = GitHub(app)

# setup session store
Session(app)

assets = Assets(app)

assets.register(
    'styles',
    Bundle(
        'scss/styles.scss',
        filters='libsass,datauri',
        output='css/styles.%(version)s.css',
        depends=('**/*.scss'),
    )
)

pages = FlatPages(app)


@app.before_request
def before_request():
    g.user_access_token = session.get('user_access_token', None)
    user_login = session.get('user_login', None)
    if g.user_access_token and not user_login:
        user_login = github.get('user').get('login', None)
        if user_login is None:
            abort(500)
        session['user_login'] = user_login
    g.user_login = user_login


@github.access_token_getter
def token_getter():
    return g.user_access_token


def add_to_org(user_login):
    """
    Adds the GitHub user with the given login to the org.
    """
    return github.put(
        'teams/%s/memberships/%s' % (GITHUB_MEMBERS_TEAM_ID, user_login),
        access_token=GITHUB_ADMIN_TOKEN
    )


def get_roadies():
    return github.get(
        'teams/%d/members' % GITHUB_ROADIES_TEAM_ID,
        access_token=GITHUB_ADMIN_TOKEN
    )


def publicize_membership(user_login):
    """
    Publicizes the membership of the GitHub user with the given login.
    """
    github.put(
        'orgs/%s/public_members/%s' % (GITHUB_ORG_ID, user_login),
        access_token=GITHUB_ADMIN_TOKEN
    )


@app.template_filter('is_member')
def is_member(user_login):
    """
    Checks if the GitHub user with the given login is member of the org.
    """
    try:
        github.get(
            'orgs/%s/members/%s' % (GITHUB_ORG_ID, user_login),
            access_token=GITHUB_ADMIN_TOKEN,
        )
        return True
    except GitHubError:
        return False


def verified_emails():
    """
    Checks if the authenticated GitHub user has any verified email addresses.
    """
    return any(
        [email for email in github.get('user/emails')
        if email.get('verified', False)],
    )


@app.errorhandler(403)
def forbidden(error):
    return render_template('forbidden.html')


@app.errorhandler(500)
def error(error):
    return render_template('error.html')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/security')
def security():
    return redirect('/docs/faq/#how-do-i-report-a-security-incident')


@app.route('/account')
def account():
    if not g.user_login:
        return redirect(url_for('login'))

    return render_template('account.html')


@app.route('/login')
def login():
    if not g.user_login:
        return github.authorize(scope=app.config['GITHUB_SCOPE'])

    if is_member(g.user_login):
        url = url_for('index')
    else:
        url = url_for('join')
    return redirect(url)


@app.route('/join')
def join():
    if not g.user_login:
        return redirect(url_for('login'))

    if is_member(g.user_login):
        return redirect(url_for('index'))

    # deny permission if there are no verified emails
    has_verified_emails = verified_emails()

    membership = None
    if has_verified_emails:
        try:
            membership = add_to_org(g.user_login)
        except GitHubError:
            pass

    return render_template(
        'join.html',
        next_url='https://github.com/orgs/jazzband/dashboard',
        membership=membership,
        org_id=GITHUB_ORG_ID,
        has_verified_emails=has_verified_emails,
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/docs', defaults={'path': 'index'})
@app.route('/docs/<path:path>')
def docs(path):
    page = pages.get_or_404(path)
    template = 'layouts/%s.html' % page.meta.get('layout', 'docs')
    return render_template(template, page=page)


@app.route('/projects')
def projects():
    projects = github.get(
        'orgs/%s/repos?type=public' % GITHUB_ORG_ID,
        access_token=GITHUB_ADMIN_TOKEN,
    )
    return render_template('projects.html', projects=projects)


@app.route('/roadies')
def roadies():
    return render_template('roadies.html', roadies=get_roadies())


@app.route('/callback')
@github.authorized_handler
def callback(access_token):
    next_url = url_for('join')

    if access_token is None:
        session.clear()
        return redirect(next_url)

    session['user_access_token'] = access_token
    return redirect(next_url)

if __name__ == '__main__':
    app.run(debug=True)
