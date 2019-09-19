import pytest
from jazzband.factory import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config["DEBUG"] = True
    app.config["VALIDATE_IP"] = False
    app.config["VALIDATE_SIGNATURE"] = False
    return app
