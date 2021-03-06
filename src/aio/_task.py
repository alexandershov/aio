import inspect
import logging
import typing as tp

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
    def __init__(self, coro, *, loop=None):
        self._coro = coro
        self._state = 'pending'
        self._future = _future.Future()
        self._aio_future_blocking: tp.Optional[_base_future.BaseFuture] = None
        self._needs_to_force_cancel = False
        if loop is None:
            loop = _loop.get_event_loop()
        self._loop = loop
        self._loop.add_task(self)
        self._loop.call_soon(self._run)
        logger.debug('Created %s', self)

    def result(self) -> object:
        return self._future.result()

    def set_result(self, result) -> None:
        raise RuntimeError(f"{self} doesn't support set_result()")

    def exception(self) -> Exception:
        return self._future.exception()

    def set_exception(self, exception) -> None:
        raise RuntimeError(f"{self} doesn't support set_exception()")

    def done(self) -> bool:
        return self._future.done()

    def add_done_callback(self, callback) -> None:
        self._future.add_done_callback(callback)

    def remove_done_callback(self, callback) -> int:
        return self._future.remove_done_callback(callback)

    def cancel(self) -> bool:
        logger.debug('Cancelling %s', self)
        if self.done():
            logger.debug("Can't cancel %s, because it's already done", self)
            return False
        self._set_needs_to_force_cancel()
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
        try:
            future = self._wake_up()
        except StopIteration as exc:
            self._mark_as_done(exc.value)
        except _errors.CancelledError:
            self._mark_as_cancelled()
        except Exception as exc:
            self._mark_as_failed(exc)
        else:
            self._block_on(future)
        self._hibernate()

    def _wake_up(self):
        self._mark_as_running()
        if self._needs_to_force_cancel:
            self._needs_to_force_cancel = False
            return self._coro.throw(_errors.CancelledError)
        return self._coro.send(None)

    def _determine_if_needs_to_force_cancel(self) -> bool:
        if self._aio_future_blocking is None:
            return True
        if self._aio_future_blocking.cancelled():
            return False
        return not self._aio_future_blocking.cancel()

    def _mark_as_done(self, result):
        logger.debug('%s is done with result %s', self, result)
        self._state = 'done'
        self._future.set_result(result)

    def _mark_as_cancelled(self):
        logger.debug('%s is cancelled', self)
        self._state = 'cancelled'
        self._future.cancel()

    def _mark_as_failed(self, exception):
        logger.debug('%s is failed with exception %s', self, exception)
        self._state = 'done'
        self._future.set_exception(exception)

    def _block_on(self, future):
        if not isinstance(future, _base_future.BaseFuture):
            raise RuntimeError(f'{future!r} is not a future')
        self._aio_future_blocking = future
        if self._needs_to_force_cancel:
            self._set_needs_to_force_cancel()
        future.add_done_callback(lambda _: self._run())

    def _set_needs_to_force_cancel(self):
        self._needs_to_force_cancel = self._determine_if_needs_to_force_cancel()
        if self._needs_to_force_cancel:
            logger.debug('Will force cancel of %s on the next waking up', self)

    def _hibernate(self):
        self.get_loop().set_current_task(None)

    def _mark_as_running(self):
        logger.debug('Running %s', self)
        self._state = 'running'
        self._aio_future_blocking = None
        self.get_loop().set_current_task(self)

    def __str__(self) -> str:
        return f'<Task {self._state} {self._coro}>'

    def __repr__(self) -> str:
        return str(self)


async def _wrap_awaitable(awaitable):
    return await awaitable
