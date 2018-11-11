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
