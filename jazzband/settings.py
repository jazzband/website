import redis
from decouple import config, Csv
from markdown.extensions.toc import TocExtension
from markdown.extensions.wikilinks import WikiLinkExtension

from .renderer import smart_pygmented_markdown

SECRET_KEY = config('SECRET_KEY', 'dev key')
DEBUG = config('DEBUG', True, cast=bool)

FLATPAGES_ROOT = '../docs'
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
GITHUB_BANNED_USERS = config('GITHUB_BANNED_USERS', '', cast=Csv())

VALIDATE_IP = False

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = 'jazzhands'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_USE_SIGNER = config('SESSION_USE_SIGNER', True, cast=bool)
SESSION_REDIS = redis.from_url(config('REDIS_URL', 'redis://127.0.0.1:6379/0'))
PERMANENT_SESSION_LIFETIME = 60 * 60
LIBSASS_STYLE = 'compressed'

SENTRY_USER_ATTRS = ['user_login']
