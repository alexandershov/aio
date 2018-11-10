import aio


class Task(aio.Future):
    def __init__(self, coro):
        super().__init__()
        self._coro = coro
        loop = aio.get_event_loop()
        loop.call_soon(self._step)

    def _step(self):
        try:
            future = self._coro.send(None)
        except StopIteration as exc:
            # TODO: do I need to call `set_result()`?
            self.set_result(exc.value)
        else:
            if not isinstance(future, aio.Future):
                raise RuntimeError(f'{future!r} is not a future')
            future.add_done_callback(lambda _: self._step())
