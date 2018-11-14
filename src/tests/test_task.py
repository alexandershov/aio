import pytest

import aio


@pytest.fixture(name='coro')
def coro_fixture(request):
    del request  # unused
    return _coro_pass()


def test_doesnt_support_set_result(coro):
    # TODO: get rid of warning '_coro_pass' was never awaited
    task = aio.Task(coro)
    with pytest.raises(RuntimeError):
        task.set_result(9)


def test_doesnt_support_set_exception(coro):
    task = aio.Task(coro)
    with pytest.raises(RuntimeError):
        task.set_exception(9)


async def _coro_pass():
    pass
