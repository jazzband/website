import time
import unicodedata
from urllib.parse import urljoin, urlparse
from collections.abc import Mapping, Iterable

from flask import current_app, request, session, url_for


def sub_dict(map: Mapping, keys: Iterable | None) -> dict:
    """Extract a subset of a mapping containing only the specified keys."""
    if not keys:
        return dict(map)
    return {key: map[key] for key in keys if key in map}


def patch_http_cache_headers(response, timeout: int | None = None):
    """Set appropriate HTTP cache headers on a response."""
    if timeout is None:
        timeout = current_app.config.get("HTTP_CACHE_TIMEOUT") or 0

    if timeout:
        response.cache_control.public = True
        response.cache_control.max_age = timeout
        response.expires = int(time.time() + timeout)
    else:
        response.cache_control.max_age = 0
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True
        response.cache_control.proxy_revalidate = True
        response.expires = -1
    return response


def full_url(url: str) -> str:
    """Convert a relative URL to a full URL using the current request's base."""
    return urljoin(request.url_root, url)


def is_safe_url(
    url: str, allowed_hosts: set[str] | None = None, require_https: bool = False
) -> bool:
    """
    Return True if the url is a safe redirection.

    A safe URL doesn't point to a different host and uses a safe scheme.
    Always returns False on an empty url.

    If require_https is True, only 'https' will be considered a valid scheme.

    Uses Python's standard library urlparse which is reliable and well-tested.
    """
    if not url or not (url := url.strip()):
        return False

    if allowed_hosts is None:
        allowed_hosts = set()

    # Chrome treats \ completely as / in paths but it could be part of some
    # basic auth credentials so we need to check both URLs.
    return _is_safe_url(
        url, allowed_hosts, require_https=require_https
    ) and _is_safe_url(
        url.replace("\\", "/"), allowed_hosts, require_https=require_https
    )


def _is_safe_url(
    url: str, allowed_hosts: set[str], require_https: bool = False
) -> bool:
    """Internal helper for is_safe_url using urllib.parse.urlparse."""
    # Chrome considers any URL with more than two slashes to be absolute, but
    # urlparse is not so flexible. Treat any url with three slashes as unsafe.
    if url.startswith("///"):
        return False

    try:
        # Use standard library urlparse which handles edge cases well
        url_info = urlparse(url)
    except ValueError:  # e.g. invalid IPv6 addresses
        return False

    # Forbid URLs like http:///example.com - with a scheme, but without a hostname.
    # In that URL, example.com is not the hostname but a path component. However,
    # Chrome will still consider example.com to be the hostname, so we must not
    # allow this syntax.
    if not url_info.netloc and url_info.scheme:
        return False

    # Forbid URLs that start with control characters. Some browsers (like
    # Chrome) ignore quite a few control characters at the start of a
    # URL and might consider the URL as scheme relative.
    if unicodedata.category(url[0])[0] == "C":
        return False

    scheme = url_info.scheme
    # Consider URLs without a scheme (e.g. //example.com/p) to be http.
    if not url_info.scheme and url_info.netloc:
        scheme = "http"

    valid_schemes = {"https"} if require_https else {"http", "https"}
    return (not url_info.netloc or url_info.netloc in allowed_hosts) and (
        not scheme or scheme in valid_schemes
    )


def get_redirect_target(default: str = "content.index") -> str:
    """
    Get a safe redirect target from various sources.

    Checks session, request args, referrer, and falls back to default.
    Only returns URLs that pass the safety check.
    """
    targets = (
        session.get("next"),
        request.args.get("next"),
        request.referrer,
        url_for(default),
    )

    for target in targets:
        if target and is_safe_url(target, allowed_hosts=None):
            return target

    # Fallback - this should always work
    return url_for(default)
