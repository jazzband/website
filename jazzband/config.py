from datetime import timedelta
import os
import redis
from decouple import config, Csv
from markdown.extensions.toc import TocExtension
from markdown.extensions.wikilinks import WikiLinkExtension

from .renderer import smart_pygmented_markdown

IS_PRODUCTION = 'PRODUCTION' in os.environ

ROOT_DIR = os.path.dirname(__file__)

SECRET_KEY = config('SECRET_KEY', 'dev key')
DEBUG = config('DEBUG', True, cast=bool)

HOSTNAMES = config('HOSTNAMES', 'localhost:5000,0.0.0.0:5000', cast=Csv())

REDIS_URL = config('REDIS_URL', 'redis://127.0.0.1:6379/0')
REDIS = redis.StrictRedis.from_url(REDIS_URL)

# how many seconds to set the expires and max_age headers
HTTP_CACHE_TIMEOUT = config('HTTP_CACHE_TIMEOUT', 60 * 60, cast=int)

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

SESSION_COOKIE_NAME = 'session'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_REFRESH_EACH_REQUEST = False
PERMANENT_SESSION_LIFETIME = timedelta(days=14)

LIBSASS_STYLE = 'compressed'

OPBEAT = {
    'HOSTNAME': 'jazzband.co',
}

SQLALCHEMY_DATABASE_URI = config(
    'DATABASE_URL',
    'postgres://jazzband:jazzband@localhost:5432/jazzband',
)
if IS_PRODUCTION:
    SQLALCHEMY_DATABASE_URI += '?sslmode=require'
    VALIDATE_IP = config('GITHUB_VALIDATE_IP', True, cast=bool)
    VALIDATE_SIGNATURE = config('GITHUB_VALIDATE_SIGNATURE', True, cast=bool)
else:
    VALIDATE_IP = False
    VALIDATE_SIGNATURE = False

SQLALCHEMY_TRACK_MODIFICATIONS = False

CSP_REPORT_URI = config('CSP_REPORT_URI', None)
CSP_REPORT_ONLY = config('CSP_REPORT_ONLY', False, cast=bool)

if 'GIT_REV' in os.environ:
    SENTRY_CONFIG = {
        'release': os.environ['GIT_REV'],
    }
    SENTRY_USER_ATTRS = ['id', 'login', 'is_banned', 'is_member']
