import logging


def _configure_logging():
    logger = logging.getLogger('aio')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# TODO: maybe it should be called when event loop is running?
_configure_logging()
