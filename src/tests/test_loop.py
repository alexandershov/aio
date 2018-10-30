import aio

import aio.loop
import pytest


@pytest.fixture(name='loop')
def loop_fixture(request):
    return aio.get_event_loop()


def test_is_running(loop):
    assert not loop.is_running()


def test_call_soon(loop):
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert not loop.is_running()


class _Stopper:
    def __init__(self, loop: aio.loop.Loop):
        self._loop = loop

    def __call__(self):
        assert self._loop.is_running()
        self._loop.stop()
