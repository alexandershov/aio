import aio
import aio.future
import pytest


def test_result():
    f = aio.Future()
    f.set_result(9)
    assert f.result() == 9


def test_done():
    f = aio.Future()
    f.set_result(9)
    assert f.done()


def test_not_done():
    f = aio.Future()
    assert not f.done()


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
