import os
import redis
from decouple import config, Csv
from markdown.extensions.toc import TocExtension
from markdown.extensions.wikilinks import WikiLinkExtension

from .renderer import smart_pygmented_markdown

ROOT_DIR = os.path.dirname(__file__)

SECRET_KEY = config('SECRET_KEY', 'dev key')
DEBUG = config('DEBUG', True, cast=bool)

HOSTNAMES = config('HOSTNAMES', 'localhost:5000,0.0.0.0:5000', cast=Csv())

CACHE_TYPE = 'redis'
CACHE_REDIS_URL = config('REDIS_URL', 'redis://127.0.0.1:6379/0')
CACHE_KEY_PREFIX = config('HEROKU_SLUG_COMMIT', '')

FLATPAGES_ABOUT_ROOT = '../docs/about'
FLATPAGES_ABOUT_EXTENSION = FLATPAGES_NEWS_EXTENSION = ['.md']
FLATPAGES_NEWS_MARKDOWN_EXTENSIONS = [
    'codehilite',
    'fenced_code',
    'footnotes',
    'admonition',
    'tables',
    'abbr',
    'smarty',
    WikiLinkExtension(base_url='/about/', end_url='', html_class=''),
]
FLATPAGES_ABOUT_MARKDOWN_EXTENSIONS = FLATPAGES_NEWS_MARKDOWN_EXTENSIONS + [
    TocExtension(permalink=True),
]

FLATPAGES_ABOUT_HTML_RENDERER = FLATPAGES_NEWS_HTML_RENDERER = \
    smart_pygmented_markdown

FLATPAGES_NEWS_ROOT = '../docs/news'

# Set these values in the .env file or env vars
GITHUB_CLIENT_ID = config('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = config('GITHUB_CLIENT_SECRET', '')
GITHUB_ORG_ID = config('GITHUB_ORG_ID', 'jazzband')
GITHUB_SCOPE = config('GITHUB_SCOPE', 'read:org,user:email')
GITHUB_MEMBERS_TEAM_ID = config('GITHUB_MEMBERS_TEAM_ID', 0, cast=int)
GITHUB_ROADIES_TEAM_ID = config('GITHUB_ROADIES_TEAM_ID', 0, cast=int)
GITHUB_ADMIN_TOKEN = config('GITHUB_ADMIN_TOKEN', '')
GITHUB_WEBHOOKS_KEY = config('GITHUB_WEBHOOKS_KEY', '')

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = 'jazzband'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_USE_SIGNER = config('SESSION_USE_SIGNER', True, cast=bool)
SESSION_REFRESH_EACH_REQUEST = False
SESSION_REDIS = redis.from_url(CACHE_REDIS_URL)
PERMANENT_SESSION_LIFETIME = 60 * 60
LIBSASS_STYLE = 'compressed'

OPBEAT = {
    'HOSTNAME': 'jazzband.co',
}

SQLALCHEMY_DATABASE_URI = config(
    'DATABASE_URL',
    'postgres://jazzband:jazzband@localhost:5432/jazzband',
)
if 'HEROKU_APP_NAME' in os.environ:
    SQLALCHEMY_DATABASE_URI += '?sslmode=require'
else:
    VALIDATE_IP = False
    VALIDATE_SIGNATURE = False

SQLALCHEMY_TRACK_MODIFICATIONS = False
