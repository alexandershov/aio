import inspect
import logging

import aio

logger = logging.getLogger(__name__)


def ensure_future(fut_or_coro):
    if inspect.iscoroutine(fut_or_coro):
        return Task(fut_or_coro)
    return fut_or_coro


class Task(aio.future.BaseFuture):
    def __init__(self, coro):
        super().__init__()
        self._coro = coro
        self._status = 'pending'
        self._future = aio.Future()
        loop = aio.get_event_loop()
        loop.call_soon(self._run)
        logger.debug('Created %s', self)

    def result(self) -> object:
        return self._future.result()

    def set_result(self, result) -> None:
        raise RuntimeError(f'{self} does not support set_result()')

    def exception(self) -> Exception:
        return self._future.exception()

    def set_exception(self, exception) -> None:
        raise RuntimeError(f'{self} does not support set_exception()')

    def done(self) -> bool:
        return self._future.done()

    def add_done_callback(self, callback) -> None:
        self._future.add_done_callback(callback)

    def _run(self):
        self._status = 'running'
        logger.debug('Running %s', self)
        try:
            future = self._coro.send(None)
        except StopIteration as exc:
            # TODO: what about if there's some exception?
            self._status = 'done'
            self._future.set_result(exc.value)
        else:
            if not isinstance(future, aio.Future):
                raise RuntimeError(f'{future!r} is not a future')
            future.add_done_callback(lambda _: self._run())

    def __str__(self) -> str:
        return f'<Task {self._status} {self._coro}>'

    def __repr__(self) -> str:
        return str(self)
