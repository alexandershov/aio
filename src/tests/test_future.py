import aio


def test_result():
    f = aio.Future()
    f.set_result(9)
    assert f.result() == 9
