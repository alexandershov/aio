import logging

import pytest

import aio


@pytest.fixture(name='future')
def future_fixture(request):
    del request  # unused
    return aio.Future()


@pytest.fixture(name='loop')
def loop_fixture(request):
    del request  # unused
    return aio.get_event_loop()


@pytest.fixture(autouse=True, scope='session')
def logging_fixture(request):
    del request  # unused
    logger = logging.getLogger('aio')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
