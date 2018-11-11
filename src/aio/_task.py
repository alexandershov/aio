import logging

import aio

logger = logging.getLogger(__name__)  # TODO: what's the best practice to create logger?


class Task(aio.Future):
    def __init__(self, coro):
        super().__init__()
        self._coro = coro
        loop = aio.get_event_loop()
        loop.call_soon(self._run)
        logger.debug('Created %s', self)

    def _run(self):
        logger.debug('Running %s', self)
        try:
            future = self._coro.send(None)
        except StopIteration as exc:
            # TODO: what about if there's some exception?
            self.set_result(exc.value)
        else:
            if not isinstance(future, aio.Future):
                raise RuntimeError(f'{future!r} is not a future')
            future.add_done_callback(lambda _: self._run())

    def __str__(self):
        return f'Task <{self._status()}, {self._coro}>'

    def _status(self):
        if self.done():
            return 'finished'
        return 'running'
