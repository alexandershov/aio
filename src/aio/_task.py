import aio


class Task(aio.Future):
    def __init__(self, coro):
        super().__init__()
        self._coro = coro
        loop = aio.get_event_loop()
        loop.call_soon(self._run, None)

    def _run(self, to_send):
        try:
            item = self._coro.send(to_send)
        except StopIteration as exc:
            self.set_result(exc.value)
        else:
            if isinstance(item, aio.Future):
                item.add_done_callback(lambda _: self._run(item.result()))
            else:
                # TODO: get rid of infinite recursion
                self._run(item)
