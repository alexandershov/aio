import aio
import aio.future
import pytest


def test_result():
    f = aio.Future()
    f.set_result(9)
    assert f.result() == 9


def test_cant_set_result_twice():
    f = aio.Future()
    f.set_result(9)
    with pytest.raises(aio.future.InvalidStateError):
        f.set_result(9)
