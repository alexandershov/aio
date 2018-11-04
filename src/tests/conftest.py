import pytest

import aio


@pytest.fixture(name='future')
def future_fixture(request):
    return aio.Future()


@pytest.fixture(name='loop')
def loop_fixture(request):
    return aio.get_event_loop()
