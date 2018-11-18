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
        self._state = 'pending'
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

    def remove_done_callback(self, callback) -> int:
        return self._future.remove_done_callback(callback)

    def cancel(self):
        # TODO: if I wait on Future, then call cancel() on this future
        if self.done():
            return False
        self._run(throw=aio.CancelledError)

    def cancelled(self) -> bool:
        return self._future.cancelled()

    def _run(self, throw=None):
        if self.done():
            logger.debug('%s is done, nothing to run', self)
            return
        self._state = 'running'
        logger.debug('Running %s', self)
        try:
            if throw is None:
                future = self._coro.send(None)
            else:
                future = self._coro.throw(throw)
        except StopIteration as exc:
            self._state = 'done'
            self._future.set_result(exc.value)
        except aio.CancelledError:
            self._state = 'cancelled'
            # TODO: I've lost traceback here
            self._future.cancel()
        except Exception as exc:
            self._state = 'done'
            self._future.set_exception(exc)
        else:
            if not isinstance(future, aio.Future):
                raise RuntimeError(f'{future!r} is not a future')
            future.add_done_callback(lambda _: self._run())

    def __str__(self) -> str:
        return f'<Task {self._state} {self._coro}>'

    def __repr__(self) -> str:
        return str(self)
