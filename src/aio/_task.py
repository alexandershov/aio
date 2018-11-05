import inspect

import aio


class Task(aio.Future):
    def __init__(self, coro):
        super().__init__()
        self._coro = coro
        loop = aio.get_event_loop()
        loop.call_soon(self._run, None)

    def _run(self, fut_or_value):
        if isinstance(fut_or_value, aio.Future):
            if fut_or_value.exception() is None:
                action = lambda: self._coro.send(fut_or_value.result())
            else:
                action = lambda: self._coro.throw(fut_or_value.exception())
        else:
            action = lambda: self._coro.send(fut_or_value)
        try:
            item = action()
        except StopIteration as exc:
            self.set_result(exc.value)
        else:
            if inspect.iscoroutine(item):
                item = Task(item)
            if isinstance(item, aio.Future):
                item.add_done_callback(lambda _: self._run(item))
            else:
                # TODO: get rid of infinite recursion
                self._run(item)
