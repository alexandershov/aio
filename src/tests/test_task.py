import pytest

import aio


def test_doesnt_support_set_result():
    task = aio.Task(_coro_pass())
    with pytest.raises(RuntimeError):
        task.set_result(9)


async def _coro_pass():
    pass
