__author__ = 'ujjwal'
import logging
from namo_app.config import get_env


if get_env() == 'production':
    #logging.basicConfig(level=logging.INFO, filename="output.log")
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
else:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)


def set_level(level="info"):
    if level.lower() == "info":
        logger.setLevel(logging.INFO)

    if level.lower() == "warning":
        logger.setLevel(logging.WARNING)

    if level.lower() == "critical":
        logger.setLevel(logging.CRITICAL)

    if level.lower() == "error":
        logger.setLevel(logging.ERROR)

    if level.lower() == "debug":
        logger.setLevel(logging.DEBUG)

