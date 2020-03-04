from flask import Blueprint

matrix = Blueprint("matrix", __name__)


@matrix.route("/.well-known/matrix/server")
def matrix_server():
    return {"m.server": "jazzband.modular.im:443"}


@matrix.route("/.well-known/matrix/client")
def matrix_client():
    return {
        "m.homeserver": {"base_url": "https://jazzband.modular.im"},
        "m.identity_server": {"base_url": "https://vector.im"},
    }
