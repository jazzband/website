from functools import wraps
from hashlib import sha1
from flask import (abort, Blueprint, render_template, redirect, request,
                   current_app, g)
from flask_flatpages import FlatPages
from jinja2 import TemplateNotFound

from ..assets import styles
from ..github import github

content = Blueprint('content', __name__)
pages = FlatPages()


def generate_etag():
    key = bytes(request.path +
                current_app.config['CACHE_KEY_PREFIX'] +
                getattr(g, 'user_login', ''))
    return sha1(key).hexdigest()


def etag(func):
    """
    Adds ETag headers
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_app.debug:
            return func(*args, **kwargs)
        etag = generate_etag()
        if request.if_none_match.contains(etag):
            return current_app.response_class(status=304)
        response = current_app.make_response(func(*args, **kwargs))
        response.set_etag(etag)
        return response
    return wrapper


@content.context_processor
def pages_context_processor():
    return {'pages': pages}


@content.route('/security')
def security():
    return redirect('/docs/faq/#how-do-i-report-a-security-incident')


@etag
@content.route('/docs', defaults={'path': 'index'})
@content.route('/docs/<path:path>')
def docs(path):
    page = pages.get_or_404(path)
    template = 'layouts/%s.html' % page.meta.get('layout', 'docs')
    return render_template(template, page=page)


@etag
@content.route('/', defaults={'page': 'index'})
@content.route('/<path:page>')
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
