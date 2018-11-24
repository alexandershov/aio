import collections
import contextlib
import logging

from . import _base_future
from . import _errors
from . import _loop

logger = logging.getLogger(__name__)

_MISSING = object()


class Future(_base_future.BaseFuture):
    def __init__(self):
        self._result = _MISSING
        self._exception: Exception = _MISSING
        self._callbacks = collections.deque()
        self._done = False
        self._cancelled = False
        self._loop = _loop.get_event_loop()

    def result(self) -> object:
        self._require_done()
        if self._has_exception():
            raise self._exception
        assert self._result is not _MISSING
        return self._result

    def set_result(self, result) -> None:
        logger.debug('Setting result of %s to %r', self, result)
        with self._transition_to_done():
            self._result = result
            self._exception = None

    def exception(self) -> Exception:
        self._require_done()
        return self._exception

    def set_exception(self, exception) -> None:
        logger.debug('Setting exception of %s to %r', self, exception)
        with self._transition_to_done():
            self._exception = _build_exception_instance(exception)

    def done(self) -> bool:
        return self._done

    def add_done_callback(self, callback) -> None:
        logger.debug('Adding done callback %s to %s', callback, self)
        self._callbacks.append(callback)
        if self.done():
            logger.debug('Immediately scheduling callbacks for %s', self)
            self._schedule_callbacks()

    def remove_done_callback(self, callback) -> int:
        new_callbacks = _with_all_occurrences_removed(self._callbacks, callback)
        num_removed = len(self._callbacks) - len(new_callbacks)
        self._callbacks = new_callbacks
        logger.debug('Removed %d callbacks equal to %s from %s', num_removed, callback, self)
        return num_removed

    def cancel(self) -> bool:
        logger.debug('Cancelling %s', self)
        if self.done():
            logger.debug("Can't cancel %s, because it's already done", self)
            return False
        self.set_exception(_errors.CancelledError)
        self._cancelled = True
        return True

    def cancelled(self) -> bool:
        return self._cancelled

    def get_loop(self) -> _loop.Loop:
        return self._loop

    def __iter__(self):
        yield self
        return self.result()

    def __await__(self):
        return (yield from self)

    def _schedule_callbacks(self):
        logger.debug('Scheduling callbacks for %s', self)
        while self._callbacks:
            self._loop.call_soon(self._callbacks.popleft(), self)

    def _require_not_done(self):
        if self.done():
            raise _errors.InvalidStateError(f'{self} is already done')

    def _require_done(self):
        if not self.done():
            raise _errors.InvalidStateError(f'{self} is not done')

    def _mark_as_done(self):
        self._done = True

    @contextlib.contextmanager
    def _transition_to_done(self):
        self._require_not_done()
        yield
        self._mark_as_done()
        self._schedule_callbacks()

    def __str__(self) -> str:
        state = self._get_state()
        return f'<Future {state}>'

    def __repr__(self) -> str:
        return str(self)

    def _has_exception(self) -> bool:
        assert self._done
        return self._result is _MISSING

    def _get_state(self) -> str:
        if not self.done():
            return 'pending'
        if self.cancelled():
            return f'cancelled'
        if self._has_exception():
            return f'exception={self._exception!r}'
        return f'result={self._result!r}'


def _build_exception_instance(exception) -> Exception:
    if isinstance(exception, Exception):
        return exception
    if _is_subclass_of_exception(exception):
        return exception()
    raise TypeError(f'{exception!r} is not an exception')


def _is_subclass_of_exception(exception) -> bool:
    return isinstance(exception, type) and issubclass(exception, Exception)


def _with_all_occurrences_removed(deque, item):
    return collections.deque(
        cur_item
        for cur_item in deque
        if cur_item != item
    )
