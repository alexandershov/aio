import aio

import aio.loop


def test_call_soon():
    loop = aio.get_event_loop()
    assert not loop.is_running()
    loop.call_soon(_Stopper(loop))
    loop.run_forever()
    assert not loop.is_running()


class _Stopper:
    def __init__(self, loop: aio.loop.Loop):
        self._loop = loop

    def __call__(self):
        assert self._loop.is_running()
        self._loop.stop()
