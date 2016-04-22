import babel.dates
from flask import Blueprint, render_template, redirect, request, url_for
from flask_flatpages import FlatPages
from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed

from .assets import styles
from .decorators import http_cache, templated

content = Blueprint('content', __name__)
about_pages = FlatPages(name='about')
news_pages = FlatPages(name='news')


def make_external(url):
    return urljoin(request.url_root, url)


@content.app_template_filter()
def format_datetime(value):
    return babel.dates.format_datetime(value)


@content.route('/join')
def join():
    return redirect(url_for('account.join'))


@content.route('/security')
def security():
    return redirect('/about/faq#how-do-i-report-a-security-incident')


@content.route('/docs', defaults={'path': 'index'})
@content.route('/docs/<path:path>')
def docs(path):
    "Just a redirect from the old URL"
    return redirect(url_for('content.about', path=path))


@content.route('/about', defaults={'path': 'index'})
@content.route('/about/<path:path>')
def about(path):
    page = about_pages.get_or_404(path)
    template = 'layouts/%s.html' % page.meta.get('layout', 'about')
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
@http_cache()
def news(path):
    page = news_pages.get_or_404(path)
    template = 'layouts/%s.html' % page.meta.get('layout', 'news_detail')
    return render_template(template, page=page)


@content.route('/')
@http_cache()
@templated()
def index():
    return {}


@content.route('/static/css/styles.css')
def styles_css():
    urls = styles.urls()
    return redirect(urls[0])
