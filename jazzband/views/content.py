import babel.dates
from dateutil import parser as dtparser
from flask import abort, Blueprint, render_template, redirect, request, url_for
from flask_flatpages import FlatPages
from jinja2 import TemplateNotFound
from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed

from ..assets import styles
from ..github import github

content = Blueprint('content', __name__)
docs_pages = FlatPages(name='docs')
news_pages = FlatPages(name='news')


@content.context_processor
def pages_context_processor():
    return {
        'docs': docs_pages,
        'news': news_pages,
    }


def make_external(url):
    return urljoin(request.url_root, url)


def parse_datetime(datetime):
    return dtparser.parse(datetime)


def format_datetime(value):
    return babel.dates.format_datetime(value)


@content.route('/security')
def security():
    return redirect('/docs/faq#how-do-i-report-a-security-incident')


@content.route('/docs', defaults={'path': 'index'})
@content.route('/docs/<path:path>')
def docs(path):
    page = docs_pages.get_or_404(path)
    template = 'layouts/%s.html' % page.meta.get('layout', 'docs')
    return render_template(template, page=page)


@content.route('/news/feed')
def news_feed():
    feed = AtomFeed('Jazzband News Feed',
                    feed_url=request.url,
                    url=request.url_root,
                    generator=None)
    for page in news_pages:
        if page.path == 'index':
            continue
        published = page.meta.get('published', None)
        updated = page.meta.get('updated', published)
        summary = page.meta.get('summary', None)
        feed.add(title=page.meta['title'],
                 content=unicode(page.html),
                 content_type='html',
                 summary=summary,
                 summary_type='text',
                 author=page.meta.get('author', None),
                 url=make_external(url_for('content.news', path=page.path)),
                 updated=updated,
                 published=published)
    return feed.get_response()


@content.route('/news', defaults={'path': 'index'})
@content.route('/news/<path:path>')
def news(path):
    page = news_pages.get_or_404(path)
    template = 'layouts/%s.html' % page.meta.get('layout', 'news_detail')
    return render_template(template, page=page)


@content.route('/', defaults={'page': 'index'})
@content.route('/<path:page>')
def show(page):
    try:
        template = 'content/%s.html' % page
        return render_template(template, docs=docs_pages, github=github)
    except TemplateNotFound:
        abort(404)


@content.route('/static/css/styles.css')
def styles_css():
    urls = styles.urls()
    return redirect(urls[0])
