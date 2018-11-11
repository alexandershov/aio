import logging


def _setup_logging():
    logger = logging.getLogger('aio')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())


# TODO: maybe it should be called when event loop is running?
_setup_logging()
