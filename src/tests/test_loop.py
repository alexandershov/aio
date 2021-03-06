import aio
import pytest


def test_get_event_loop():
    assert aio.get_event_loop() is aio.get_event_loop()


def test_fresh_loop_is_not_running(loop):
    assert not loop.is_running()


def test_str(loop):
    assert str(loop) == '<Loop pending>'


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
    loop.call_at(now - 0.0001, lambda: calls.append('first'))
    loop.call_at(now + 0.0002, lambda: calls.append('second'))
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


def test_future_add_done_callback(loop, future):
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


def test_future_remove_done_callback(loop, future):
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


def test_run_until_complete(loop, future):
    loop.call_soon(future.set_result, 9)
    assert loop.run_until_complete(future) == 9
    assert future.result() == 9


def test_run_until_complete_with_forever_pending_future(loop, future):
    loop.call_soon(loop.stop)
    with pytest.raises(RuntimeError):
        loop.run_until_complete(future)


def test_coroutine(loop):
    assert loop.run_until_complete(_sleep(0.0001)) is None


def test_coroutine_exception(loop):
    task = aio.Task(_coro_raising(ZeroDivisionError))
    with pytest.raises(ZeroDivisionError):
        loop.run_until_complete(task)
    with pytest.raises(ZeroDivisionError):
        task.result()


def test_nested_coroutine(loop):
    assert loop.run_until_complete(_coro_add(1, 2)) == 3


def test_coroutine_with_failed_future(loop, future):
    loop.call_soon(future.set_exception, ZeroDivisionError)
    exc = loop.run_until_complete(_wait_and_catch(future))
    assert isinstance(exc, ZeroDivisionError)


def test_coroutine_with_done_future(loop, future):
    loop.call_soon(future.set_result, 9)
    result = loop.run_until_complete(_wait_and_catch(future))
    assert result == 9


def test_coroutine_with_task(loop):
    inner_task = aio.ensure_future(_coro_returning(9))
    task = aio.Task(_wait(inner_task))
    assert loop.run_until_complete(task) == 9


def test_exception_handler(loop):
    num_exceptions = 0

    def _counting_exception_handler(_loop, context):
        del context  # unused
        nonlocal num_exceptions
        num_exceptions += 1

    loop.set_exception_handler(_counting_exception_handler)
    loop.call_soon(_raising, ZeroDivisionError)
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert not loop.is_running()
    assert num_exceptions == 1


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


def test_get_running_loop_when_no_loop_exists():
    aio.set_event_loop(None)
    with pytest.raises(RuntimeError):
        aio.get_running_loop()


def test_get_running_loop_when_no_loop_is_running():
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


def test_cancel_task_cancels_future_blocking(loop, future):
    task = aio.Task(_wait(future))
    loop.call_soon(task.cancel)
    with pytest.raises(aio.CancelledError):
        loop.run_until_complete(task)
    assert future.cancelled()


def test_cancel_task_blocking_on_done_future(loop, future):
    task = aio.Task(_wait_and_sleep_after_cancel(future))
    loop.call_soon(future.set_result, 9)
    loop.call_soon(task.cancel)
    assert loop.run_until_complete(task) == -9
    assert not future.cancelled()
    assert not task.cancelled()


def test_cancel_itself(loop, future):
    task = aio.Task(_coro_cancel_itself(future))
    with pytest.raises(aio.CancelledError):
        loop.run_until_complete(task)


def test_cancel_itself_after_await(loop, future):
    task = aio.Task(_coro_cancel_itself_after_sleep(future))
    with pytest.raises(aio.CancelledError):
        loop.run_until_complete(task)


def test_run():
    assert aio.run(_coro_returning(9)) == 9


def test_run_future(future):
    with pytest.raises(ValueError):
        aio.run(future)


def test_close(loop):
    loop.close()
    assert loop.is_closed()


def test_cant_run_forever_after_close(loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.run_forever()


def test_cant_run_until_complete_after_close(loop, future):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.run_until_complete(future)


def test_cant_run_call_soon_after_close(loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.call_soon(print, 'impossible')


def test_cant_run_call_later_after_close(loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.call_later(0.0001, print, 'impossible')


def test_cant_run_call_at_after_close(loop):
    loop.close()
    with pytest.raises(RuntimeError):
        loop.call_at(loop.time(), print, 'impossible')


def test_cant_close_running_loop():
    with pytest.raises(RuntimeError):
        aio.run(_coro_close_running_loop())


def test_task_get_loop(loop):
    coro = _coro_pass()
    task = aio.Task(coro)
    assert task.get_loop() is loop
    coro.close()


def test_future_get_loop(loop):
    future = aio.Future()
    assert future.get_loop() is loop


def test_current_task(loop):
    task = aio.Task(_coro_return_current_task())
    assert loop.run_until_complete(task) is task


def test_current_task_in_call_soon(loop):
    tasks = []
    loop.call_soon(lambda: tasks.append(aio.current_task()))
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert tasks == [None]


def test_current_task_on_not_running_loop():
    with pytest.raises(RuntimeError):
        aio.current_task()


def test_current_task_on_explicit_non_running_loop(loop):
    assert aio.current_task(loop) is None


def test_all_tasks(loop):
    tasks = []
    task = aio.Task(_coro_append_all_tasks(tasks))
    loop.run_until_complete(task)
    assert tasks == [{task}]


def test_ensure_future_on_coroutine(loop):
    task = aio.ensure_future(_coro_returning(9))
    assert isinstance(task, aio.Task)
    assert loop.run_until_complete(task) == 9


def test_ensure_future_on_awaitable(loop, future):
    task = aio.ensure_future(_Awaitable(future))
    assert isinstance(task, aio.Task)
    loop.call_soon(future.set_result, 9)
    assert loop.run_until_complete(task) == 9


class _Awaitable:
    def __init__(self, future):
        self._future = future

    def __await__(self):
        result = yield from self._future
        return result


async def _wait_and_sleep_after_cancel(future):
    try:
        await future
    except aio.CancelledError:
        await _sleep(0.0001)
        return -9
    else:
        return future.result()


async def _coro_append_all_tasks(tasks):
    tasks.append(set(aio.all_tasks()))


async def _coro_return_current_task():
    return aio.current_task()


async def _coro_close_running_loop():
    aio.get_running_loop().close()


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


def _raising(exception):
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


async def _coro_raising(exception):
    raise exception


async def _coro_add(x, y):
    await _sleep(0.0001)
    return x + y


async def _sleep(duration):
    future = aio.Future()
    loop = aio.get_event_loop()
    loop.call_later(duration, _set_result_if_not_cancelled, future, None)
    await future


def _set_result_if_not_cancelled(future, result):
    if not future.cancelled():
        future.set_result(result)


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


async def _coro_cancel_itself(future):
    aio.current_task().cancel()
    await future


async def _coro_cancel_itself_after_sleep(future):
    await _sleep(0.0001)
    aio.current_task().cancel()
    await future
