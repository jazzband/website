import logging
import os

logger = logging.getLogger(__name__)


if 'SENTRY_DSN' in os.environ:
    from raven.contrib.flask import Sentry
    sentry = Sentry(logging=True, level=logging.INFO)
else:
    class FakeSentry:
        def init_app(self, *args, **kwargs):
            pass

        def captureMessage(self, message, *args, **kwargs):
            logger.info(message, *args, **kwargs)

        def captureException(self, *args, **kwargs):
            logger.exception('Error')

    sentry = FakeSentry()  # noqa
