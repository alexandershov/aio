import aio

import aio.loop
import pytest


@pytest.fixture(name='loop')
def loop_fixture(request):
    return aio.get_event_loop()


def test_get_event_loop():
    assert aio.get_event_loop() is aio.get_event_loop()


def test_is_running(loop):
    assert not loop.is_running()


def test_call_soon(loop):
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert not loop.is_running()


def test_call_later(loop):
    calls = []
    loop.call_later(0.0002, lambda: calls.append('second'))
    loop.call_later(0.0001, lambda: calls.append('first'))
    loop.call_later(0.0003, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first', 'second']


def test_call_at(loop):
    calls = []
    now = loop.time()
    loop.call_at(now + 0.0002, lambda: calls.append('second'))
    loop.call_at(now + 0.0001, lambda: calls.append('first'))
    loop.call_at(now + 0.0003, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first', 'second']


def test_callback_ordering(loop):
    calls = []
    now = loop.time()
    loop.call_at(now + 0.0002, lambda: calls.append('second'))
    loop.call_at(now + 0.0002, _Stopper(loop))
    loop.call_at(now + 0.0001, lambda: calls.append('first'))
    loop.run_forever()
    assert calls == ['first', 'second']


def test_call_soon_with_arguments(loop):
    calls = []
    loop.call_soon(lambda arg: arg.append('first'), calls)
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert calls == ['first']


def test_call_later_with_arguments(loop):
    calls = []
    loop.call_later(0.0001, lambda arg: arg.append('first'), calls)
    loop.call_later(0.0001, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first']


class _Stopper:
    def __init__(self, loop: aio.loop.Loop):
        self._loop = loop

    def __call__(self):
        assert self._loop.is_running()
        self._loop.stop()
