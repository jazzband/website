import datetime
import time
from functools import wraps
from flask import abort, Blueprint, render_template, redirect, make_response
from flask_flatpages import FlatPages
from jinja2 import TemplateNotFound
from wsgiref.handlers import format_date_time

from ..assets import styles
from ..github import github

content = Blueprint('content', __name__)
pages = FlatPages()


def cache(timeout=None):
    """
    Add Flask cache response headers based on expires in seconds.

    If expires is None, caching will be disabled.
    Otherwise, caching headers are set to expire in now + expires seconds

    Example usage:

    @app.route('/map')
    @cache(expires=60)
    def index():
      return render_template('index.html')

    Original: https://gist.github.com/glenrobertson/954da3acec84606885f5
    """
    def cache_decorator(view):
        @wraps(view)
        def cache_func(*args, **kwargs):
            now = datetime.datetime.now()

            response = make_response(view(*args, **kwargs))
            last_modified = time.mktime(now.timetuple())
            response.headers['Last-Modified'] = format_date_time(last_modified)

            if timeout is None:
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
                response.headers['Expires'] = '-1'
            else:
                expires_time = now + datetime.timedelta(seconds=timeout)
                response.headers['Cache-Control'] = 'public'
                expires = time.mktime(expires_time.timetuple())
                response.headers['Expires'] = format_date_time(expires)

            return response
        return cache_func
    return cache_decorator


@content.context_processor
def pages_context_processor():
    return {'pages': pages}


@content.route('/security')
def security():
    return redirect('/docs/faq/#how-do-i-report-a-security-incident')


@content.route('/docs', defaults={'path': 'index'})
@content.route('/docs/<path:path>')
@cache(60 * 60)
def docs(path):
    page = pages.get_or_404(path)
    template = 'layouts/%s.html' % page.meta.get('layout', 'docs')
    return render_template(template, page=page)


@content.route('/', defaults={'page': 'index'})
@content.route('/<path:page>')
@cache(60 * 60)
def show(page):
    try:
        return render_template(
            'content/%s.html' % page,
            pages=pages,
            github=github,
        )
    except TemplateNotFound:
        abort(404)


@content.route('/static/css/styles.css')
def styles_css():
    urls = styles.urls()
    return redirect(urls[0])
