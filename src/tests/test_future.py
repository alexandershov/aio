import aio
import pytest


def test_result(future):
    future.set_result(9)
    assert future.result() == 9


def test_done_after_set_result(future):
    future.set_result(9)
    assert future.done()


def test_fresh_future_not_done(future):
    assert not future.done()


def test_cant_set_result_twice(future):
    future.set_result(9)
    with pytest.raises(aio.InvalidStateError):
        future.set_result(9)


def test_cant_get_missing_result(future):
    with pytest.raises(aio.InvalidStateError):
        future.result()


def test_exception(future):
    future.set_exception(ZeroDivisionError())
    assert isinstance(future.exception(), ZeroDivisionError)


def test_set_exception_via_class(future):
    future.set_exception(ZeroDivisionError)
    assert isinstance(future.exception(), ZeroDivisionError)


def test_done_after_set_exception(future):
    future.set_exception(ZeroDivisionError)
    assert future.done()


def test_cant_set_exception_twice(future):
    future.set_exception(ZeroDivisionError)
    with pytest.raises(aio.InvalidStateError):
        future.set_exception(ZeroDivisionError)


def test_cant_get_missing_exception(future):
    with pytest.raises(aio.InvalidStateError):
        future.exception()


def test_result_after_set_exception(future):
    future.set_exception(ZeroDivisionError)
    with pytest.raises(ZeroDivisionError):
        future.result()


def test_exception_is_none_after_set_result(future):
    future.set_result(9)
    assert future.exception() is None


def test_cancel(future):
    assert future.cancel() is True
    assert future.cancelled()
    assert future.done()
    assert isinstance(future.exception(), aio.CancelledError)
    with pytest.raises(aio.CancelledError):
        future.result()


def test_cancel_twice(future):
    future.cancel()
    assert future.cancel() is False
    assert future.cancelled()


def test_cancel_after_done(future):
    future.set_result(9)
    assert future.cancel() is False
    assert not future.cancelled()


def test_str_after_cancel(future):
    future.cancel()
    assert str(future) == '<Future cancelled>'


@pytest.mark.parametrize('exception', [
    9,
    int,
])
def test_invalid_exception_in_set_exception(future, exception):
    with pytest.raises(TypeError):
        future.set_exception(exception)
    assert not future.done()


def test_remove_non_existing_done_callback(future):
    assert future.remove_done_callback(_do_nothing_callback) == 0


def test_get_loop():
    loop = aio.new_event_loop()
    future = aio.Future(loop=loop)
    assert future.get_loop() is loop


def _do_nothing_callback(future):
    del future  # unused
