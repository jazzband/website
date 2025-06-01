"""
Tests for utility functions in jazzband.utils module.

These tests cover URL safety validation, redirect target handling,
cache header patching, and other utility functions.
"""

from flask import url_for, session, request
from time import time

from jazzband.utils import (
    sub_dict,
    patch_http_cache_headers,
    full_url,
    is_safe_url,
    get_redirect_target,
    _is_safe_url,
)


def test_sub_dict_with_valid_keys():
    """Test sub_dict returns subset of dictionary with valid keys."""
    original = {"a": 1, "b": 2, "c": 3, "d": 4}
    keys = ["a", "c"]

    result = sub_dict(original, keys)

    assert result == {"a": 1, "c": 3}


def test_sub_dict_with_empty_keys():
    """Test sub_dict returns original dict when keys is empty."""
    original = {"a": 1, "b": 2}
    keys = []

    result = sub_dict(original, keys)

    assert result == original


def test_sub_dict_with_nonexistent_keys():
    """Test sub_dict ignores keys that don't exist in the dictionary."""
    original = {"a": 1, "b": 2}
    keys = ["a", "x", "y"]

    result = sub_dict(original, keys)

    assert result == {"a": 1}


def test_sub_dict_with_none_keys():
    """Test sub_dict returns original dict when keys is None."""
    original = {"a": 1, "b": 2}
    keys = None

    result = sub_dict(original, keys)

    assert result == original


def test_patch_http_cache_headers_with_timeout(app, mocker):
    """Test patch_http_cache_headers sets caching headers when timeout is provided."""
    with app.test_request_context():
        response = mocker.MagicMock()
        response.cache_control = mocker.MagicMock()
        timeout = 3600

        mocker.patch('jazzband.utils.time.time', return_value=1000)
        result = patch_http_cache_headers(response, timeout)

        assert result == response
        assert response.cache_control.public is True
        assert response.cache_control.max_age == timeout
        assert response.expires == int(1000 + timeout)


def test_patch_http_cache_headers_without_timeout(app, mocker):
    """Test patch_http_cache_headers sets no-cache headers when timeout is None."""
    with app.test_request_context():
        # Explicitly set HTTP_CACHE_TIMEOUT to None to test the None case
        app.config["HTTP_CACHE_TIMEOUT"] = None

        response = mocker.MagicMock()
        response.cache_control = mocker.MagicMock()

        result = patch_http_cache_headers(response, timeout=None)

        assert result == response
        assert response.cache_control.max_age == 0
        assert response.cache_control.no_cache is True
        assert response.cache_control.no_store is True
        assert response.cache_control.must_revalidate is True
        assert response.cache_control.proxy_revalidate is True
        assert response.expires == -1


def test_patch_http_cache_headers_uses_config_timeout(app, mocker):
    """Test patch_http_cache_headers uses HTTP_CACHE_TIMEOUT from config."""
    app.config["HTTP_CACHE_TIMEOUT"] = 1800
    with app.test_request_context():
        response = mocker.MagicMock()
        response.cache_control = mocker.MagicMock()

        mocker.patch('jazzband.utils.time.time', return_value=2000)
        result = patch_http_cache_headers(response)

        assert response.cache_control.public is True
        assert response.cache_control.max_age == 1800


def test_full_url(app):
    """Test full_url creates absolute URLs from relative ones."""
    with app.test_request_context("http://example.com/"):
        result = full_url("/test/path")

        assert result == "http://example.com/test/path"


def test_is_safe_url_with_safe_relative_url():
    """Test is_safe_url returns True for safe relative URLs."""
    url = "/safe/path"
    allowed_hosts = {"example.com"}

    result = is_safe_url(url, allowed_hosts)

    assert result is True


def test_is_safe_url_with_safe_absolute_url():
    """Test is_safe_url returns True for safe absolute URLs on allowed hosts."""
    url = "http://example.com/path"
    allowed_hosts = {"example.com"}

    result = is_safe_url(url, allowed_hosts)

    assert result is True


def test_is_safe_url_with_unsafe_host():
    """Test is_safe_url returns False for URLs on disallowed hosts."""
    url = "http://evil.com/path"
    allowed_hosts = {"example.com"}

    result = is_safe_url(url, allowed_hosts)

    assert result is False


def test_is_safe_url_with_empty_url():
    """Test is_safe_url returns False for empty URLs."""
    url = ""
    allowed_hosts = {"example.com"}

    result = is_safe_url(url, allowed_hosts)

    assert result is False


def test_is_safe_url_with_whitespace_url():
    """Test is_safe_url handles URLs with whitespace."""
    url = "  /safe/path  "
    allowed_hosts = {"example.com"}

    result = is_safe_url(url, allowed_hosts)

    assert result is True


def test_is_safe_url_with_https_required():
    """Test is_safe_url with require_https=True."""
    https_url = "https://example.com/path"
    http_url = "http://example.com/path"
    allowed_hosts = {"example.com"}

    assert is_safe_url(https_url, allowed_hosts, require_https=True) is True
    assert is_safe_url(http_url, allowed_hosts, require_https=True) is False


def test_is_safe_url_with_backslash_attack():
    """Test is_safe_url handles backslash-based attacks."""
    url = "http://example.com\\@evil.com/path"
    allowed_hosts = {"example.com"}

    result = is_safe_url(url, allowed_hosts)

    # Should check both the original and the backslash-replaced version
    assert result is False


def test_is_safe_url_with_triple_slash():
    """Test _is_safe_url returns False for URLs with triple slashes."""
    url = "///example.com/path"
    allowed_hosts = {"example.com"}

    result = _is_safe_url(url, allowed_hosts)

    assert result is False


def test_is_safe_url_with_control_characters():
    """Test _is_safe_url returns False for URLs starting with control characters."""
    url = "\x00http://example.com/path"
    allowed_hosts = {"example.com"}

    result = _is_safe_url(url, allowed_hosts)

    assert result is False


def test_is_safe_url_with_scheme_no_hostname():
    """Test _is_safe_url returns False for URLs with scheme but no hostname."""
    url = "http:///example.com/path"
    allowed_hosts = {"example.com"}

    result = _is_safe_url(url, allowed_hosts)

    assert result is False


def test_get_redirect_target_from_session(app):
    """Test get_redirect_target uses session 'next' value."""
    with app.test_request_context():
        session["next"] = "/safe/path"

        result = get_redirect_target()

        assert result == "/safe/path"


def test_get_redirect_target_from_request_args(app):
    """Test get_redirect_target uses request args 'next' value."""
    with app.test_request_context("/?next=/safe/path"):
        result = get_redirect_target()

        assert result == "/safe/path"


def test_get_redirect_target_from_referrer(app):
    """Test get_redirect_target uses request referrer."""
    with app.test_request_context(headers={"Referer": "/safe/path"}):
        result = get_redirect_target()

        assert result == "/safe/path"


def test_get_redirect_target_default(app):
    """Test get_redirect_target returns default URL when no safe target found."""
    with app.test_request_context():
        result = get_redirect_target()

        assert result == url_for("content.index")


def test_get_redirect_target_custom_default(app):
    """Test get_redirect_target uses custom default."""
    with app.test_request_context():
        result = get_redirect_target(default="account.dashboard")

        assert result == url_for("account.dashboard")


def test_get_redirect_target_unsafe_url(app):
    """Test get_redirect_target skips unsafe URLs."""
    with app.test_request_context():
        session["next"] = "http://evil.com/path"

        result = get_redirect_target()

        assert result == url_for("content.index")


def test_get_redirect_target_empty_values(app):
    """Test get_redirect_target skips empty values."""
    with app.test_request_context():
        session["next"] = ""

        result = get_redirect_target()

        assert result == url_for("content.index")
