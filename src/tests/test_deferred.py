import aio


def test_callback():
    d = aio.Deferred()
    d.add_callback(lambda result: result + 1)
    d.callback(8)
    assert d.result == 9


def test_two_callbacks():
    d = aio.Deferred()
    d.add_callback(lambda result: result + 1)
    d.add_callback(lambda result: result * 2)
    d.callback(8)
    assert d.result == 18
