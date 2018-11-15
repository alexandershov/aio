import aio
import pytest


# TODO: use fresh loop in tests after set_event_loop is implemented
def test_get_event_loop():
    assert aio.get_event_loop() is aio.get_event_loop()


def test_fresh_loop_is_not_running(loop):
    assert not loop.is_running()


def test_call_soon(loop):
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert not loop.is_running()


def test_call_later(loop):
    calls = []
    loop.call_later(0.0001, lambda: calls.append('first'))
    loop.call_later(0.0002, lambda: calls.append('second'))
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
    loop.call_soon(lambda seq, item: seq.append(item),
                   calls, 'first')
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert calls == ['first']


def test_call_later_with_arguments(loop):
    calls = []
    loop.call_later(0.0001,
                    lambda seq, item: seq.append(item),
                    calls, 'first')
    loop.call_later(0.0001, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first']


def test_call_at_with_arguments(loop):
    calls = []
    now = loop.time()
    loop.call_at(now + 0.0001,
                 lambda seq, item: seq.append(item),
                 calls, 'first')
    loop.call_at(now + 0.0001, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first']


def test_add_done_callback(future, loop):
    results = []
    future.add_done_callback(lambda f: results.append(f.result()))
    future.add_done_callback(lambda f: loop.stop())
    loop.call_soon(lambda: future.set_result(9))
    loop.run_forever()
    assert results == [9]


def test_run_until_complete(future, loop):
    loop.call_soon(lambda: future.set_result(9))
    assert loop.run_until_complete(future) == 9
    assert future.result() == 9


def test_run_until_complete_with_forever_pending_future(future, loop):
    loop.call_soon(loop.stop)
    with pytest.raises(RuntimeError):
        loop.run_until_complete(future)


def test_coroutine(loop):
    assert loop.run_until_complete(_sleep(0.0001)) is None


def test_coroutine_exception(loop):
    task = aio.Task(_coro_zero_division())
    with pytest.raises(ZeroDivisionError):
        loop.run_until_complete(task)
    with pytest.raises(ZeroDivisionError):
        task.result()


def test_nested_coroutine(loop):
    assert loop.run_until_complete(_coro_add(1, 2)) == 3


def test_coroutine_with_failed_future(future, loop):
    loop.call_soon(future.set_exception, ZeroDivisionError)
    exc = loop.run_until_complete(_wait(future))
    assert isinstance(exc, ZeroDivisionError)


def test_coroutine_with_done_future(future, loop):
    loop.call_soon(future.set_result, 9)
    result = loop.run_until_complete(_wait(future))
    assert result == 9


async def _wait(future):
    try:
        result = await future
    except Exception as exc:
        return exc
    else:
        return result


async def _coro_zero_division():
    return 1 / 0


async def _coro_add(x, y):
    await _sleep(0.0001)
    return x + y


async def _sleep(duration):
    future = aio.Future()
    loop = aio.get_event_loop()
    loop.call_later(duration, future.set_result, None)
    await future


class _Stopper:
    def __init__(self, loop: aio.Loop):
        self._loop = loop

    def __call__(self):
        assert self._loop.is_running()
        self._loop.stop()
