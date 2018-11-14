import pytest

import aio


@pytest.fixture(name='coro')
def coro_fixture(request):
    del request  # unused
    coro = _coro_pass()
    yield coro
    coro.close()


def test_doesnt_support_set_result(coro):
    task = aio.Task(coro)
    with pytest.raises(RuntimeError):
        task.set_result(9)


def test_doesnt_support_set_exception(coro):
    task = aio.Task(coro)
    with pytest.raises(RuntimeError):
        task.set_exception(9)


async def _coro_pass():
    pass
