from urllib.parse import urljoin, urlparse
from time import time
from flask import current_app, request, url_for


def sub_dict(map, keys):
    if not keys:
        return map
    return {key: map[key] for key in keys if key in map}


def patch_http_cache_headers(response, timeout=None):
    if timeout is None:
        timeout = current_app.config.get('HTTP_CACHE_TIMEOUT') or 0

    if timeout:
        response.cache_control.public = True
        response.cache_control.max_age = timeout
        response.expires = int(time() + timeout)
    else:
        response.cache_control.max_age = 0
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True
        response.cache_control.proxy_revalidate = True
        response.expires = -1
    return response


def full_url(url):
    return urljoin(request.url_root, url)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc)
