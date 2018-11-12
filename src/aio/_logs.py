import logging


def _configure_logging():
    logger = logging.getLogger('aio')
    logger.addHandler(logging.NullHandler())


# TODO: look at when `requests` calls it
_configure_logging()
