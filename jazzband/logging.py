import logging
from flask.logging import default_handler

for name in ["jazzband", "spinach"]:
    logger = logging.getLogger(name)
    logger.addHandler(default_handler)
    logger.setLevel(logging.INFO)
