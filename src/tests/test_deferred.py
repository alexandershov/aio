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


def test_callback_returning_deferred():
    d = aio.Deferred()
    adder = _adder(5)
    d.add_callback(lambda unused_result: adder)
    d.add_callback(lambda result: result * 2)
    d.callback(8)
    adder.callback(1)
    assert adder.result is None
    assert d.result == 12


def _adder(x):
    d = aio.Deferred()
    d.add_callback(lambda result: result + x)
    return d
