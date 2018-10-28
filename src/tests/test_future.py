import aio
import aio.future
import pytest


@pytest.fixture(name='future')
def future_fixture(request):
    return aio.Future()


def test_result(future):
    future.set_result(9)
    assert future.result() == 9


def test_done(future):
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
    future.set_exception(ValueError())
    assert isinstance(future.exception(), ValueError)


def test_set_exception_via_class(future):
    future.set_exception(ValueError)
    assert isinstance(future.exception(), ValueError)
