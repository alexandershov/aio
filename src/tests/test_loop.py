import aio


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


def test_coroutine(loop):
    assert loop.run_until_complete(sleep(0.0001)) is None


def test_nested_coroutine(loop):
    assert loop.run_until_complete(coro_add(1, 2)) == 3


def test_coroutine_failed_future(future, loop):
    loop.call_soon(future.set_exception, ZeroDivisionError)
    exc = loop.run_until_complete(wait(future))
    assert isinstance(exc, ZeroDivisionError)


async def wait(future):
    try:
        await future
    except Exception as exc:
        return exc
    else:
        return None


async def coro_add(x, y):
    await sleep(0.0001)
    return x + y


async def sleep(duration):
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
