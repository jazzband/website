from time import time
from flask import current_app


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
