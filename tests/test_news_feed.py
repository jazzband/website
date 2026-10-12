from xml.etree import ElementTree

from flask import Flask
from jinja2 import DictLoader
import pytest

from jazzband import content


@pytest.fixture
def news_app(tmp_path, monkeypatch):
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        FLATPAGES_NEWS_ROOT=str(tmp_path),
        FLATPAGES_NEWS_EXTENSION=[".md"],
    )
    app.jinja_loader = DictLoader(
        {"layouts/news_detail.html": "{{ page.html | safe }}"}
    )
    monkeypatch.setattr(content, "news_pages", content.NewsFlatPages(app, name="news"))
    app.register_blueprint(content.content)
    return app


@pytest.mark.parametrize("preserve_feed", [True, False])
def test_article_edits_preserve_only_opted_in_feed_content(
    news_app, tmp_path, preserve_feed
):
    """A snapshot freezes syndication, while the article always uses its current body."""
    article = tmp_path / "2026" / "03" / "14" / "example.md"
    article.parent.mkdir(parents=True)
    metadata = "title: Example\npublished: 2026-03-14T12:00:00+01:00\n\n"
    article.write_text(metadata + "Original article.", encoding="utf-8")

    with news_app.test_client() as client:
        before = client.get("/news/feed")
        assert before.status_code == 200
        if preserve_feed:
            article.with_suffix(".feed.html").write_text(
                "<p>Original article.</p>", encoding="utf-8"
            )

        article.write_text(metadata + "Rewritten **article**.", encoding="utf-8")
        content.news_pages.reload()
        after = client.get("/news/feed")
        page = client.get("/news/2026/03/14/example")

    assert page.status_code == 200
    assert page.data == b"<p>Rewritten <strong>article</strong>.</p>"
    assert after.status_code == 200
    entry = ElementTree.fromstring(after.data).find(
        "{http://www.w3.org/2005/Atom}entry"
    )
    if preserve_feed:
        assert after.data == before.data
        expected_content = "<p>Original article.</p>"
    else:
        assert after.data != before.data
        expected_content = "<p>Rewritten <strong>article</strong>.</p>"
    assert entry.findtext("{http://www.w3.org/2005/Atom}content") == expected_content
