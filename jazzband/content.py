import datetime

import babel.dates
from feedgen.feed import FeedGenerator
from flask import (
    Blueprint,
    Response,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_flatpages import FlatPages
from flask_login import current_user
import pytz
from werkzeug.security import safe_join

from .decorators import templated
from .utils import full_url


content = Blueprint("content", __name__)
about_pages = FlatPages(name="about")


class NewsFlatPages(FlatPages):
    def __iter__(self):
        pages = super().__iter__()
        # Articles are pages with a publication date
        articles = (p for p in pages if "published" in p.meta)
        # Show the 10 most recent articles, most recent first.
        latest = sorted(articles, reverse=True, key=lambda page: page.meta["published"])
        for page in latest:
            published = page.meta.get("published", None)
            if published and published.tzinfo is None:
                published = pytz.utc.localize(published)
            page.meta["published_date"] = published
            yield page


news_pages = NewsFlatPages(name="news")


@content.app_template_filter()
def format_datetime(value):
    return babel.dates.format_datetime(value)


@content.route("/join")
def join():
    return redirect(url_for("account.join"))


@content.route("/security")
def security():
    return redirect("/about/security")


@content.route("/security.txt")
def securitytxt_redirect():
    return redirect(url_for("content.securitytxt_file"))


@content.route("/.well-known/security.txt")
def securitytxt_file():
    return send_from_directory(
        current_app.static_folder,
        "security.txt",
        as_attachment=False,
        mimetype="text/plain",
    )


@content.route("/donate")
def donate():
    return redirect("https://psfmember.org/civicrm/contribute/transact?reset=1&id=34")


@content.route("/docs", defaults={"path": "index"})
@content.route("/docs/<path:path>")
def docs(path):
    "Just a redirect from the old URL"
    return redirect(url_for("content.about", path=path))


@content.route("/about", defaults={"path": "index"})
@content.route("/about/<path:path>")
def about(path):
    page = about_pages.get_or_404(path)
    layout = page.meta.get("layout", "about")
    template = f"layouts/{layout}.html"
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
    layout = page.meta.get("layout", "news_detail")
    template = f"layouts/{layout}.html"
    return render_template(template, page=page)


@content.route("/")
@templated()
def index():
    if current_user.is_authenticated:
        return redirect(url_for("account.dashboard"))
    return {}


@content.route("/favicon.ico")
def favicon():
    return send_from_directory(
        safe_join(current_app.static_folder, "favicons"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
