import pytest

import aio


def test_doesnt_support_set_result():
    # TODO: get rid of warning '_coro_pass' was never awaited
    task = aio.Task(_coro_pass())
    with pytest.raises(RuntimeError):
        task.set_result(9)


def test_doesnt_support_set_exception():
    task = aio.Task(_coro_pass())
    with pytest.raises(RuntimeError):
        task.set_exception(9)


async def _coro_pass():
    pass
