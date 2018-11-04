import pytest

import aio


@pytest.fixture(name='future')
def future_fixture(request):
    return aio.Future()
