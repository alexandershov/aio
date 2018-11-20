import logging

import pytest

import aio


@pytest.fixture(name='future')
def future_fixture(request):
    del request  # unused
    return aio.Future()


@pytest.fixture(name='loop', autouse=True)
def loop_fixture(request):
    del request  # unused
    loop = aio.new_event_loop()
    aio.set_event_loop(loop)
    return loop


@pytest.fixture(autouse=True, scope='session')
def logging_fixture(request):
    logger = logging.getLogger('aio')
    level = _get_logging_level(request)
    if level is not None:
        logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def _get_logging_level(request):
    level_name = request.config.getoption('--log-level')
    if level_name is None:
        return None
    if not hasattr(logging, level_name):
        raise RuntimeError(f'Unknown log level: {level_name}')
    return getattr(logging, level_name)
