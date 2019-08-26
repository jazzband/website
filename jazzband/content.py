import datetime

import babel.dates
import pytz
from feedgen.feed import FeedGenerator
from flask import (
    Blueprint,
    Response,
    current_app,
    render_template,
    redirect,
    request,
    url_for,
    send_from_directory,
    safe_join,
)
from flask_flatpages import FlatPages
from flask_login import current_user

from .assets import styles
from .decorators import templated
from .utils import full_url

content = Blueprint("content", __name__)
about_pages = FlatPages(name="about")
news_pages = FlatPages(name="news")


@content.app_template_filter()
def format_datetime(value):
    return babel.dates.format_datetime(value)


@content.route("/join")
def join():
    return redirect(url_for("account.join"))


@content.route("/security")
def security():
    return redirect("/about/contact#security")


@content.route("/docs", defaults={"path": "index"})
@content.route("/docs/<path:path>")
def docs(path):
    "Just a redirect from the old URL"
    return redirect(url_for("content.about", path=path))


@content.route("/about", defaults={"path": "index"})
@content.route("/about/<path:path>")
def about(path):
    page = about_pages.get_or_404(path)
    template = "layouts/%s.html" % page.meta.get("layout", "about")
    return render_template(template, page=page)


@content.route("/news/feed")
def news_feed():
    feed = FeedGenerator()
    feed.id("https://jazzband.co/news/feed")
    feed.link(href="https://jazzband.co/", rel="alternate")
    feed.title("Jazzband News Feed")
    feed.subtitle("We are all part of this.")
    feed.link(href=full_url(request.url), rel="self")

    # the list of updates of all news for setting the feed's updated value
    updates = []

    for page in news_pages:
        if page.path == "index":
            continue

        # make the datetime timezone aware if needed
        published = page.meta.get("published", None)
        if published and published.tzinfo is None:
            published = pytz.utc.localize(published)
        updated = page.meta.get("updated", published)
        if updated:
            if updated.tzinfo is None:
                updated = pytz.utc.localize(updated)
            updates.append(updated)

        summary = page.meta.get("summary", None)
        author = page.meta.get("author", None)
        author_link = page.meta.get("author_link", None)
        url = full_url(url_for("content.news", path=page.path))

        entry = feed.add_entry()
        entry.id(url)
        entry.title(page.meta["title"])
        entry.summary(summary)
        entry.content(content=str(page.html), type="html")

        if author is not None:
            author = {"name": author}
            if author_link is not None:
                author["uri"] = author_link
            entry.author(author)

        entry.link(href=url)
        entry.updated(updated)
        entry.published(published)

    sorted_updates = sorted(updates)
    feed.updated(sorted_updates and sorted_updates[-1] or datetime.utcnow())

    return Response(feed.atom_str(pretty=True), mimetype="application/atom+xml")


@content.route("/news", defaults={"path": "index"})
@content.route("/news/<path:path>")
def news(path):
    page = news_pages.get_or_404(path)
    template = "layouts/%s.html" % page.meta.get("layout", "news_detail")
    return render_template(template, page=page)


@content.route("/")
@templated()
def index():
    if current_user.is_authenticated:
        return redirect(url_for("account.dashboard"))
    return {}


@content.route("/static/css/styles.css")
def styles_css():
    urls = styles.urls()
    return redirect(urls[0])


@content.route("/favicon.ico")
def favicon():
    filename = "favicon.ico"
    cache_timeout = current_app.get_send_file_max_age(filename)
    favicon_path = safe_join(current_app.static_folder, "favicons")
    return send_from_directory(
        favicon_path,
        filename,
        mimetype="image/vnd.microsoft.icon",
        cache_timeout=cache_timeout,
    )
