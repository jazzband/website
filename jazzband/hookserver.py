# -*- coding: utf-8 -*-
"""
Flask-Hookserver: GitHub webhooks using Flask.

:copyright: (c) 2016 by Nick Frost.
:license: MIT, see LICENSE for more details.
"""

from functools import wraps
import hashlib
import hmac
import ipaddress
import time

from flask import request
import requests
from werkzeug.exceptions import BadRequest, Forbidden, ServiceUnavailable
import werkzeug.security


__author__ = "Nick Frost"
__version__ = "1.1.0"
__license__ = "MIT"


class Hooks(object):
    """The Hooks object registers handlers to GitHub webhooks events.

    :param app: the optional :class:`~flask.Flask` instance to register
                the extension
    :param url: the url that events will be posted to
    """

    def __init__(self, app=None, url="/hooks"):
        """Initialize the extension."""
        self._hooks = {}
        if app is not None:
            self.init_app(app, url=url)

    def init_app(self, app, url="/hooks"):
        """Register the URL route to the application.

        :param app: the optional :class:`~flask.Flask` instance to
                register the extension
        :param url: the url that events will be posted to
        """
        app.config.setdefault("VALIDATE_IP", True)
        app.config.setdefault("VALIDATE_SIGNATURE", True)

        @app.route(url, methods=["POST"])
        def hook():
            if app.config["VALIDATE_IP"]:
                if not is_github_ip(request.remote_addr):
                    raise Forbidden("Requests must originate from GitHub")

            if app.config["VALIDATE_SIGNATURE"]:
                key = app.config.get("GITHUB_WEBHOOKS_KEY", app.secret_key)
                signature = request.headers.get("X-Hub-Signature")

                if hasattr(request, "get_data"):
                    # Werkzeug >= 0.9
                    payload = request.get_data()
                else:
                    payload = request.data

                if not signature:
                    raise BadRequest("Missing signature")

                if not check_signature(signature, key, payload):
                    raise BadRequest("Wrong signature")

            event = request.headers.get("X-GitHub-Event")
            guid = request.headers.get("X-GitHub-Delivery")
            if not event:
                raise BadRequest("Missing header: X-GitHub-Event")
            elif not guid:
                raise BadRequest("Missing header: X-GitHub-Delivery")

            if hasattr(request, "get_json"):
                # Flask >= 0.10
                data = request.get_json()
            else:
                data = request.json

            if event in self._hooks:
                return self._hooks[event](data, guid)
            else:
                return "Hook not used\n"

    def register_hook(self, hook_name, fn):
        """Register a function to be called on a GitHub event."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = fn
        else:
            raise Exception("%s hook already registered" % hook_name)

    def hook(self, hook_name):
        """A decorator that's used to register a new hook handler.

        :param hook_name: the event to handle
        """

        def wrapper(fn):
            self.register_hook(hook_name, fn)
            return fn

        return wrapper


class _timed_memoize(object):
    """Decorator that caches the value of function.

    Does not care about arguments to the function, will still only cache
    one value.
    """

    def __init__(self, timeout):
        """Initialize with timeout in seconds."""
        self.timeout = timeout
        self.last = None
        self.cache = None

    def __call__(self, fn):
        """Create the wrapped function."""

        @wraps(fn)
        def inner(*args, **kwargs):
            if self.last is None or time.time() - self.last > self.timeout:
                self.cache = fn(*args, **kwargs)
                self.last = time.time()
            return self.cache

        return inner


def _load_github_hooks(github_url="https://api.github.com"):
    """Request GitHub's IP block from their API.

    Return the IP network.

    If we detect a rate-limit error, raise an error message stating when
    the rate limit will reset.

    If something else goes wrong, raise a generic 503.
    """
    try:
        resp = requests.get(github_url + "/meta")
        if resp.status_code == 200:
            return resp.json()["hooks"]
        else:
            if resp.headers.get("X-RateLimit-Remaining") == "0":
                reset_ts = int(resp.headers["X-RateLimit-Reset"])
                reset_string = time.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(reset_ts)
                )
                raise ServiceUnavailable(
                    "Rate limited from GitHub until " + reset_string
                )
            else:
                raise ServiceUnavailable("Error reaching GitHub")
    except (KeyError, ValueError, requests.exceptions.ConnectionError) as err:
        raise ServiceUnavailable("Error reaching GitHub") from err


# So we don't get rate limited
load_github_hooks = _timed_memoize(60)(_load_github_hooks)


def is_github_ip(ip_str):
    """Verify that an IP address is owned by GitHub."""
    if isinstance(ip_str, bytes):
        ip_str = ip_str.decode()

    ip = ipaddress.ip_address(ip_str)
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    for block in load_github_hooks():
        if ip in ipaddress.ip_network(block):
            return True
    return False


def check_signature(signature, key, data):
    """Compute the HMAC signature and test against a given hash."""
    if isinstance(key, type("")):
        key = key.encode()

    digest = "sha1=" + hmac.new(key, data, hashlib.sha1).hexdigest()

    # Covert everything to byte sequences
    if isinstance(digest, type("")):
        digest = digest.encode()
    if isinstance(signature, type("")):
        signature = signature.encode()

    return werkzeug.security.safe_str_cmp(digest, signature)
