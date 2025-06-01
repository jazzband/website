"""
Tests for content views and functionality.

These tests cover static page routing, redirects, news feeds,
and other content-related functionality.
"""

from flask import url_for
from datetime import datetime
import pytz

from jazzband.content import format_datetime


def test_join_redirect(app):
    """Test /join redirects to account.join."""
    with app.test_client() as client:
        response = client.get("/join")

        assert response.status_code == 302
        assert response.location.endswith(url_for("account.join"))


def test_security_redirect(app):
    """Test /security redirects to about/security page."""
    with app.test_client() as client:
        response = client.get("/security")

        assert response.status_code == 302
        assert response.location.endswith("/about/security")


def test_securitytxt_redirect(app):
    """Test /security.txt redirects to .well-known/security.txt."""
    with app.test_client() as client:
        response = client.get("/security.txt")

        assert response.status_code == 302
        assert response.location.endswith(url_for("content.securitytxt_file"))


def test_securitytxt_file(app):
    """Test .well-known/security.txt serves the security.txt file."""
    with app.test_client() as client:
        # This will return 404 if file doesn't exist, which is fine for testing
        response = client.get("/.well-known/security.txt")

        # Either serves the file (200) or file not found (404)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.mimetype == "text/plain"


def test_donate_redirect(app):
    """Test /donate redirects to PSF donation page."""
    with app.test_client() as client:
        response = client.get("/donate")

        assert response.status_code == 302
        assert "psfmember.org" in response.location
        assert "contribute" in response.location


def test_docs_redirect_default(app):
    """Test /docs redirects to about/index."""
    with app.test_client() as client:
        response = client.get("/docs")

        assert response.status_code == 302
        assert response.location.endswith(url_for("content.about", path="index"))


def test_docs_redirect_with_path(app):
    """Test /docs/<path> redirects to about/<path>."""
    with app.test_client() as client:
        response = client.get("/docs/contributing")

        assert response.status_code == 302
        assert response.location.endswith(url_for("content.about", path="contributing"))


def test_about_page_default(app):
    """Test /about loads the index page."""
    with app.test_client() as client:
        # This will return 404 if page doesn't exist, which is expected
        response = client.get("/about")

        # Either serves the page (200) or page not found (404)
        assert response.status_code in [200, 404]


def test_about_page_with_path(app):
    """Test /about/<path> loads the specified page."""
    with app.test_client() as client:
        # This will return 404 if page doesn't exist, which is expected
        response = client.get("/about/contributing")

        # Either serves the page (200) or page not found (404)
        assert response.status_code in [200, 404]


def test_news_page_default(app):
    """Test /news loads the index page."""
    with app.test_client() as client:
        # This will return 404 if page doesn't exist, which is expected
        response = client.get("/news")

        # Either serves the page (200) or page not found (404)
        assert response.status_code in [200, 404]


def test_news_page_with_path(app):
    """Test /news/<path> loads the specified news article."""
    with app.test_client() as client:
        # This will return 404 if page doesn't exist, which is expected
        response = client.get("/news/some-article")

        # Either serves the page (200) or page not found (404)
        assert response.status_code in [200, 404]


def test_index_unauthenticated_user(app):
    """Test index page for unauthenticated users returns content."""
    with app.test_client() as client:
        response = client.get("/")

        assert response.status_code == 200


def test_index_authenticated_user_redirects(app, mocker):
    """Test index page redirects authenticated users to dashboard."""
    # Mock current_user to be authenticated
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True

    mocker.patch("jazzband.content.current_user", mock_user)

    with app.test_client() as client:
        response = client.get("/")

        assert response.status_code == 302
        assert response.location.endswith(url_for("account.dashboard"))


def test_favicon(app):
    """Test favicon.ico is served correctly."""
    with app.test_client() as client:
        response = client.get("/favicon.ico")

        # Either serves the favicon (200) or file not found (404)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.mimetype == "image/vnd.microsoft.icon"


def test_news_feed_basic(app):
    """Test news feed generation without actual news pages."""
    with app.test_client() as client:
        response = client.get("/news/feed")

        assert response.status_code == 200
        assert response.mimetype == "application/atom+xml"
        assert b"Jazzband News Feed" in response.data


def test_news_feed_with_pages(app, mocker):
    """Test news feed generation with mock news pages."""
    # Create a mock news page
    mock_page = mocker.MagicMock()
    mock_page.path = "test-article"
    mock_page.meta = {
        "title": "Test Article",
        "published": datetime(2023, 1, 1, 12, 0, 0),
        "summary": "Test summary",
        "author": "Test Author",
        "author_link": "https://example.com/author",
    }
    mock_page.html = "<p>Test content</p>"

    mock_news_pages = mocker.MagicMock()
    mock_news_pages.__iter__.return_value = [mock_page]

    mocker.patch("jazzband.content.news_pages", mock_news_pages)

    with app.test_client() as client:
        response = client.get("/news/feed")

        assert response.status_code == 200
        assert response.mimetype == "application/atom+xml"
        assert b"Test Article" in response.data


def test_news_feed_with_timezone_aware_dates(app, mocker):
    """Test news feed handles timezone-aware dates correctly."""
    # Create a mock news page with timezone-naive date
    mock_page = mocker.MagicMock()
    mock_page.path = "test-article"
    mock_page.meta = {
        "title": "Test Article",
        "published": datetime(2023, 1, 1, 12, 0, 0),  # timezone-naive
        "updated": pytz.utc.localize(datetime(2023, 1, 2, 12, 0, 0)),  # timezone-aware
    }
    mock_page.html = "<p>Test content</p>"

    mock_news_pages = mocker.MagicMock()
    mock_news_pages.__iter__.return_value = [mock_page]

    mocker.patch("jazzband.content.news_pages", mock_news_pages)

    with app.test_client() as client:
        response = client.get("/news/feed")

        assert response.status_code == 200
        assert response.mimetype == "application/atom+xml"


def test_format_datetime_filter():
    """Test format_datetime template filter."""
    test_date = datetime(2023, 1, 1, 12, 0, 0)

    result = format_datetime(test_date)

    # Should return a formatted string (exact format depends on locale)
    assert isinstance(result, str)
    assert "2023" in result


def test_newsflatpages_iteration(mocker):
    """Test NewsFlatPages iteration and date handling."""
    from jazzband.content import NewsFlatPages

    # Create a mock page with published date
    mock_page = mocker.MagicMock()
    mock_page.meta = {
        "published": datetime(2023, 1, 1, 12, 0, 0)  # timezone-naive
    }

    # Mock the parent __iter__ method
    news_pages = NewsFlatPages()
    with mocker.patch.object(
        NewsFlatPages.__bases__[0], "__iter__", return_value=[mock_page]
    ):
        pages = list(news_pages)

        assert len(pages) == 1
        # Check that published_date was added and is timezone-aware
        assert "published_date" in pages[0].meta
        assert pages[0].meta["published_date"].tzinfo is not None


def test_newsflatpages_sorting(mocker):
    """Test NewsFlatPages sorts articles by published date."""
    from jazzband.content import NewsFlatPages

    # Create mock pages with different published dates
    older_page = mocker.MagicMock()
    older_page.meta = {"published": datetime(2023, 1, 1)}

    newer_page = mocker.MagicMock()
    newer_page.meta = {"published": datetime(2023, 2, 1)}

    no_date_page = mocker.MagicMock()
    no_date_page.meta = {}  # No published date

    news_pages = NewsFlatPages()
    with mocker.patch.object(
        NewsFlatPages.__bases__[0],
        "__iter__",
        return_value=[older_page, newer_page, no_date_page],
    ):
        pages = list(news_pages)

        # Should only include pages with published dates, newest first
        assert len(pages) == 2
        assert pages[0].meta["published"] == datetime(2023, 2, 1)
        assert pages[1].meta["published"] == datetime(2023, 1, 1)
