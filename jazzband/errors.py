import logging
from flask import render_template

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from spinach.contrib.sentry_sdk_spinach import SpinachIntegration


def init_app(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("error.html"), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("forbidden.html"), 403

    @app.errorhandler(500)
    def error(error):
        return render_template("error.html"), 500

    sentry_sdk.init(
        integrations=[
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR,  # Send errors as events
            ),
            FlaskIntegration(),
            SpinachIntegration(),
        ],
        request_bodies="always",
        with_locals=True,
    )
