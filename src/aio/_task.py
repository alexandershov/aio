import inspect

import aio


class Task(aio.Future):
    def __init__(self, coro):
        super().__init__()
        self._coro = coro
        loop = aio.get_event_loop()
        loop.call_soon(self._run)

    def _run(self):
        try:
            item = self._coro.send(None)
        except StopIteration as exc:
            self.set_result(exc.value)
        else:
            if inspect.iscoroutine(item):
                item = Task(item)
            if isinstance(item, aio.Future):
                item.add_done_callback(lambda _: self._run())
            else:
                raise RuntimeError(f'{item!r} is not a future or coroutine')
