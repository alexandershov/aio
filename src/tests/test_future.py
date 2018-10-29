import aio
import aio.future
import pytest


@pytest.fixture(name='future')
def future_fixture(request):
    return aio.Future()


def test_result(future):
    future.set_result(9)
    assert future.result() == 9


def test_done_after_set_result(future):
    future.set_result(9)
    assert future.done()


def test_not_done(future):
    assert not future.done()


def test_cant_set_result_twice(future):
    future.set_result(9)
    with pytest.raises(aio.future.InvalidStateError):
        future.set_result(9)


def test_cant_get_missing_result(future):
    with pytest.raises(aio.future.InvalidStateError):
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
    with pytest.raises(aio.future.InvalidStateError):
        future.set_exception(ZeroDivisionError)


def test_cant_get_missing_exception(future):
    with pytest.raises(aio.future.InvalidStateError):
        future.exception()


def test_result_after_set_exception(future):
    future.set_exception(ZeroDivisionError)
    with pytest.raises(ZeroDivisionError):
        future.result()


def test_exception_is_none_after_set_exception(future):
    future.set_result(9)
    assert future.exception() is None


@pytest.mark.parametrize('exception', [
    9,
])
def test_invalid_exception_in_set_exception(future, exception):
    with pytest.raises(TypeError):
        future.set_exception(exception)
