from flask import abort, Blueprint, render_template, redirect
from flask_flatpages import FlatPages
from jinja2 import TemplateNotFound

from ..github import github

content = Blueprint('content', __name__)
pages = FlatPages()


@content.context_processor
def pages_context_processor():
    return {'pages': pages}


@content.route('/security')
def security():
    return redirect('/docs/faq/#how-do-i-report-a-security-incident')


@content.route('/docs', defaults={'path': 'index'})
@content.route('/docs/<path:path>')
def docs(path):
    page = pages.get_or_404(path)
    template = 'layouts/%s.html' % page.meta.get('layout', 'docs')
    return render_template(template, page=page)


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
