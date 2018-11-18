import aio
import pytest


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
    loop.call_later(-0.0001, lambda: calls.append('first'))
    loop.call_later(0.0002, lambda: calls.append('second'))
    loop.call_later(0.0003, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first', 'second']


def test_call_at(loop):
    calls = []
    now = loop.time()
    loop.call_at(now + 0.0002, lambda: calls.append('second'))
    loop.call_at(now - 0.0001, lambda: calls.append('first'))
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
    loop.call_soon(calls.append, 'first')
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert calls == ['first']


def test_call_later_with_arguments(loop):
    calls = []
    loop.call_later(0.0001, calls.append, 'first')
    loop.call_later(0.0001, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first']


def test_call_at_with_arguments(loop):
    calls = []
    now = loop.time()
    loop.call_at(now + 0.0001, calls.append, 'first')
    loop.call_at(now + 0.0001, _Stopper(loop))
    loop.run_forever()
    assert calls == ['first']


def test_future_add_done_callback(future, loop):
    results = []
    future.add_done_callback(lambda f: results.append(f.result()))
    future.add_done_callback(lambda f: loop.stop())
    loop.call_soon(future.set_result, 9)
    loop.run_forever()
    assert results == [9]


def test_task_add_done_callback(loop):
    results = []
    task = aio.Task(_coro_returning(9))
    task.add_done_callback(lambda f: results.append(f.result()))
    task.add_done_callback(lambda f: loop.stop())
    loop.run_forever()
    assert results == [9]


def test_future_remove_done_callback(future, loop):
    results = []

    def add_result(f):
        results.append(f.result())

    future.add_done_callback(add_result)
    future.add_done_callback(add_result)
    future.add_done_callback(lambda f: loop.stop())
    assert future.remove_done_callback(add_result) == 2
    loop.call_soon(future.set_result, 9)
    loop.run_forever()
    assert results == []


def test_task_remove_done_callback(loop):
    results = []

    def add_result(f):
        results.append(f.result())

    task = aio.Task(_coro_pass())
    task.add_done_callback(add_result)
    task.add_done_callback(add_result)
    assert task.remove_done_callback(add_result) == 2
    loop.run_until_complete(task)
    assert results == []


def test_run_until_complete(future, loop):
    loop.call_soon(future.set_result, 9)
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
    exc = loop.run_until_complete(_wait_and_catch(future))
    assert isinstance(exc, ZeroDivisionError)


def test_coroutine_with_done_future(future, loop):
    loop.call_soon(future.set_result, 9)
    result = loop.run_until_complete(_wait_and_catch(future))
    assert result == 9


def test_callback_exception(loop):
    loop.call_soon(_always_raises, ZeroDivisionError)
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert not loop.is_running()


def test_call_soon_handle(loop):
    handle = loop.call_soon(loop.stop)
    assert not handle.cancelled()
    handle.cancel()
    assert handle.cancelled()


def test_call_at_handle_when(loop):
    now = loop.time()
    when = now + 0.001
    handle = loop.call_at(when, loop.stop)
    assert handle.when() == when
    loop.run_forever()


def test_call_later_handle_when(loop):
    now = loop.time()
    handle = loop.call_later(0.001, loop.stop)
    assert handle.when() >= now + 0.0001
    loop.run_forever()


def test_cancel_call_soon(loop):
    calls = []
    handle = loop.call_soon(calls.append, 'first')
    handle.cancel()
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert calls == []


def test_cancel_call_later(loop):
    calls = []
    handle = loop.call_later(0.0001, calls.append, 'first')
    handle.cancel()
    loop.call_later(0.0001, _Stopper(loop))
    loop.run_forever()
    assert calls == []


def test_cancel_call_at(loop):
    calls = []
    now = loop.time()
    handle = loop.call_at(now + 0.0001, calls.append, 'first')
    handle.cancel()
    loop.call_at(now + 0.0001, _Stopper(loop))
    loop.run_forever()
    assert calls == []


def test_stop_calls_ready_callbacks(loop):
    calls = []
    loop.call_soon(_Stopper(loop))
    loop.call_soon(calls.append, 'first')
    loop.call_later(0, calls.append, 'second')
    loop.run_forever()
    assert calls == ['first', 'second']


def test_is_running_during_stopping(loop):
    loop.call_soon(_Stopper(loop))
    loop.call_soon(_assert_is_running, loop)
    loop.run_forever()


def test_get_running_loop(loop):
    loop.call_soon(lambda: _assert_is(aio.get_running_loop(), loop))
    loop.call_soon(_Stopper(loop))
    loop.run_forever()


def test_get_running_loop_while_no_loop_is_running():
    with pytest.raises(RuntimeError):
        aio.get_running_loop()


def test_new_event_loop():
    x = aio.new_event_loop()
    y = aio.new_event_loop()
    assert x != y


def test_set_event_loop():
    loop = aio.new_event_loop()
    aio.set_event_loop(loop)
    assert aio.get_event_loop() is loop
    loop.call_soon(_Stopper(loop))
    loop.run_forever()


def test_get_event_loop_after_unset():
    aio.set_event_loop(None)
    with pytest.raises(RuntimeError):
        aio.get_event_loop()
    aio.set_event_loop(aio.new_event_loop())


def test_cancel_task(loop):
    task = aio.Task(_coro_pass())
    assert task.cancel() is True
    with pytest.raises(aio.CancelledError):
        loop.run_until_complete(task)
    assert task.cancelled()
    assert task.cancel() is False


def test_cancel_task_blocking_on_future(loop):
    task = aio.Task(_coro_ignoring_cancelled_error())
    loop.call_soon(task.cancel)
    assert loop.run_until_complete(task) == -9


def test_cancel_task_cancels_future_blocking(future, loop):
    task = aio.Task(_wait(future))
    loop.call_soon(task.cancel)
    with pytest.raises(aio.CancelledError):
        loop.run_until_complete(task)
    assert future.cancelled()


def test_run():
    assert aio.run(_coro_returning(9)) == 9
    _restore_event_loop()


def test_run_future(future):
    with pytest.raises(ValueError):
        aio.run(future)
    _restore_event_loop()


def test_close(loop):
    loop.close()
    assert loop.is_closed()


def test_cant_run_forever_after_close(loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.run_forever()
    _restore_event_loop()


def test_cant_run_until_complete_after_close(future, loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.run_until_complete(future)
    _restore_event_loop()


def test_cant_run_call_soon_after_close(loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.call_soon(print, 'impossible')
    _restore_event_loop()


def test_cant_run_call_later_after_close(loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.call_later(0.0001, print, 'impossible')
    _restore_event_loop()


def test_cant_run_call_at_after_close(loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.call_at(loop.time(), print, 'impossible')
    _restore_event_loop()


def _restore_event_loop():
    aio.set_event_loop(aio.new_event_loop())


async def _coro_ignoring_cancelled_error():
    try:
        await _sleep(0.0001)
    except aio.CancelledError:
        return -9
    else:
        return 9


def _assert_is(x, y):
    assert x is y


def _assert_is_running(loop):
    assert loop.is_running()


def _always_raises(exception):
    raise exception


async def _wait_and_catch(future):
    try:
        result = await future
    except Exception as exc:
        return exc
    else:
        return result


async def _wait(future):
    return await future


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


async def _coro_pass():
    pass


async def _coro_returning(result):
    return result


class _Stopper:
    def __init__(self, loop: aio.Loop):
        self._loop = loop

    def __call__(self):
        assert self._loop.is_running()
        self._loop.stop()
