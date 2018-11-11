import logging

import aio

logger = logging.getLogger(__name__)  # TODO: what's the best practice to create logger?


class Task(aio.Future):
    def __init__(self, coro):
        super().__init__()
        self._coro = coro
        loop = aio.get_event_loop()
        loop.call_soon(self._run)

    def _run(self):
        try:
            future = self._coro.send(None)
        except StopIteration as exc:
            # TODO: what about if there's some exception?
            self.set_result(exc.value)
        else:
            if not isinstance(future, aio.Future):
                raise RuntimeError(f'{future!r} is not a future')
            future.add_done_callback(lambda _: self._run())
