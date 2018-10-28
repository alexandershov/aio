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


def test_cant_set_result_twice():
    f = aio.Future()
    f.set_result(9)
    with pytest.raises(aio.future.InvalidStateError):
        f.set_result(9)


def test_cant_get_missing_result():
    f = aio.Future()
    with pytest.raises(aio.future.InvalidStateError):
        f.result()


def test_exception():
    f = aio.Future()
    f.set_exception(ValueError())
    assert isinstance(f.exception(), ValueError)
