import aio


def test_callback():
    d = aio.Deferred()
    d.add_callback(lambda result: result + 1)
    d.callback(8)
    assert d.result == 9
