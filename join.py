from decouple import config
from flask import (Flask, request, g, session, redirect, url_for, abort,
                   render_template)
from flask.ext.github import GitHub, GitHubError
from flask.ext.session import Session
import redis

# Set these values in the .env file or env vars
GITHUB_CLIENT_ID = config('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = config('GITHUB_CLIENT_SECRET', '')
GITHUB_ORG_ID = config('GITHUB_ORG_ID', 'jazzband')
GITHUB_SCOPE = config('GITHUB_SCOPE', 'read:org,user:email')
GITHUB_TEAM_ID = config('GITHUB_TEAM_ID', 0, cast=int)
GITHUB_ADMIN_TOKEN = config('GITHUB_ADMIN_TOKEN', '')

SECRET_KEY = config('SECRET_KEY', 'dev key')
DEBUG = config('DEBUG', False, cast=bool)

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = 'jazzhands'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_USE_SIGNER = config('SESSION_USE_SIGNER', True, cast=bool)
SESSION_REDIS = redis.from_url(config('REDIS_URL', 'redis://127.0.0.1:6379/0'))
PERMANENT_SESSION_LIFETIME = 60 * 60

# setup flask
app = Flask(__name__)

# load decoupled config variables
app.config.from_object(__name__)

# setup github-flask
github = GitHub(app)

# setup session store
Session(app)


@app.before_request
def before_request():
    g.user_access_token = session.get('user_access_token', None)


@github.access_token_getter
def token_getter():
    return g.user_access_token


def add_to_org(user_login):
    """
    Adds the GitHub user with the given login to the org.
    """
    github.put(
        'teams/%s/memberships/%s' % (GITHUB_TEAM_ID, user_login),
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
def forbidden():
    return render_template('forbidden.html')


@app.errorhandler(500)
def error():
    return render_template('error.html')


@app.route('/')
def start():
    if g.user_access_token:
        user_login = github.get('user').get('login', None)

        # fail if something went wrong
        if user_login is None:
            abort(500)

        session['user_login'] = user_login

        # deny permission if there are no verified emails
        if not verified_emails():
            abort(403)

        membership = None
        user_is_member = is_member(user_login)

        if not user_is_member:
            try:
                membership = add_to_org(user_login)
            except GitHubError:
                pass

        return render_template(
            'index.html',
            next_url='https://join.jazzband.co/finish',
            membership=membership,
            org_id=GITHUB_ORG_ID,
            is_member=user_is_member,
        )
    else:
        return github.authorize(scope=app.config['GITHUB_SCOPE'])


@app.route('/callback')
@github.authorized_handler
def callback(access_token):
    next_url = url_for('start')

    if access_token is None:
        session.clear()
        return redirect(next_url)

    session['user_access_token'] = access_token
    return redirect(next_url)


@app.route('finish')
def finish():
    user_login = session.get('user_login', None)
    if user_login:
        try:
            publicize_membership(user_login)
        except GitHubError:
            pass
    return redirect('https://github.com/jazzband')


if __name__ == '__main__':
    app.run(debug=True)
