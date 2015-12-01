from flask import g, current_app

from flask.ext.cache import Cache

cache = Cache()


def cache_or_not():
    return bool(g.user_login) or current_app.config.get('DEBUG', False)
