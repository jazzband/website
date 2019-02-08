import logging
from flask.logging import default_handler

for logger in (
    logging.getLogger('spinach'),
):
    logger.addHandler(default_handler)
    logger.setLevel(logging.INFO)
