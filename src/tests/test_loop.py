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


def test_call_later(loop):
    calls = []
    loop.call_later(0.002, lambda: calls.append(2))
    loop.call_later(0.001, lambda: calls.append(1))
    loop.call_later(0.003, _Stopper(loop))
    loop.run_forever()
    assert calls == [1, 2]


def test_call_at(loop):
    calls = []
    now = loop.time()
    loop.call_at(now + 0.002, lambda: calls.append('second'))
    loop.call_at(now + 0.001, lambda: calls.append('first'))
    loop.call_at(now + 0.003, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first', 'second']


class _Stopper:
    def __init__(self, loop: aio.loop.Loop):
        self._loop = loop

    def __call__(self):
        assert self._loop.is_running()
        self._loop.stop()
