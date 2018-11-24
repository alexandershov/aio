import inspect
import logging

from . import _base_future
from . import _errors
from . import _future
from . import _loop

logger = logging.getLogger(__name__)


def ensure_future(obj):
    if isinstance(obj, _base_future.BaseFuture):
        return obj
    elif inspect.iscoroutine(obj):
        return Task(obj)
    elif inspect.isawaitable(obj):
        return Task(_wrap_awaitable(obj))
    else:
        raise TypeError(f'{obj!r} should be Future, coroutine, or awaitable')


def current_task(loop=None):
    if loop is None:
        loop = _loop.get_running_loop()
    return loop.current_task()


def all_tasks(loop=None):
    if loop is None:
        loop = _loop.get_running_loop()
    return loop.all_tasks()


class Task(_base_future.BaseFuture):
    def __init__(self, coro):
        self._coro = coro
        self._state = 'pending'
        self._future = _future.Future()
        self._cancelling = False
        self._aio_future_blocking = None
        self._loop = _loop.get_event_loop()
        self._loop.add_task(self)
        self._loop.call_soon(self._run)
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

    def cancel(self) -> bool:
        if self.done():
            return False
        self._cancelling = True
        self._loop.call_soon(self._run)
        return True

    def cancelled(self) -> bool:
        return self._future.cancelled()

    def get_loop(self) -> _loop.Loop:
        return self._loop

    def __iter__(self):
        yield self
        return self.result()

    def __await__(self):
        return (yield from self)

    def _run(self):
        if self.done():
            logger.debug('%s is done, nothing to run', self)
            return
        self.get_loop().set_current_task(self)
        self._state = 'running'
        logger.debug('Running %s', self)
        try:
            future = self._continue_coro()
        except StopIteration as exc:
            self._state = 'done'
            self._future.set_result(exc.value)
        except _errors.CancelledError:
            self._state = 'cancelled'
            self._future.cancel()
        except _WaitForCancel:
            pass
        except Exception as exc:
            self._state = 'done'
            self._future.set_exception(exc)
        else:
            if not isinstance(future, _base_future.BaseFuture):
                raise RuntimeError(f'{future!r} is not a future')
            self._aio_future_blocking = future
            future.add_done_callback(lambda _: self._run())
        if self._cancelling:
            self._cancelling = False
        self.get_loop().set_current_task(None)

    def _continue_coro(self):
        if self._cancelling:
            if self._aio_future_blocking is None:
                return self._coro.throw(_errors.CancelledError)
            if not self._aio_future_blocking.cancel():
                return self._coro.throw(_errors.CancelledError)
            raise _WaitForCancel
        return self._coro.send(None)

    def __str__(self) -> str:
        return f'<Task {self._state} {self._coro}>'

    def __repr__(self) -> str:
        return str(self)


async def _wrap_awaitable(awaitable):
    return await awaitable


class _WaitForCancel(Exception):
    pass
