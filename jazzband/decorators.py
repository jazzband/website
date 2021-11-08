from functools import wraps

from flask import make_response, render_template, request
from flask_login import current_user

from .utils import patch_http_cache_headers


def templated(template=None):
    """
    Taken from https://flask.palletsprojects.com/en/0.12.x/patterns/viewdecorators/
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint.replace(".", "/") + ".html"
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)

        return decorated_function

    return decorator


def http_cache(timeout=None):
    """
    Add Flask cache response headers based on timeout in seconds.

    If timeout is None, caching will be disabled.
    Otherwise, caching headers are set to expire in now + timeout seconds

    Example usage:

    @app.route('/map')
    @http_cache(timeout=60)
    def index():
      return render_template('index.html')

    Originally from https://gist.github.com/glenrobertson/954da3acec84606885f5
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            if current_user.is_authenticated:
                return response
            else:
                return patch_http_cache_headers(response, timeout)

        return decorated_function

    return decorator
