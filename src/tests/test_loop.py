import aio


def test_call_soon():
    loop = aio.get_event_loop()
    loop.call_soon(loop.stop)
    loop.run_forever()
