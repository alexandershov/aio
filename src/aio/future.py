import collections
import contextlib
import logging

from . import _loop

logger = logging.getLogger(__name__)


class BaseError(Exception):
    pass


class InvalidStateError(BaseError):
    pass


_MISSING = object()


# TODO: add BaseFuture interface, so Future & Task will inherit from it
class Future:
    def __init__(self):
        self._result = _MISSING
        self._exception: Exception = _MISSING
        self._done = False
        self._callbacks = collections.deque()

    def result(self) -> object:
        self._validate_done()
        if self._has_failed():
            raise self._exception
        return self._result

    def set_result(self, result) -> None:
        with self._transition_to_done():
            self._result = result
            self._exception = None

    def exception(self) -> Exception:
        self._validate_done()
        return self._exception

    def set_exception(self, exception) -> None:
        with self._transition_to_done():
            self._exception = _build_exception_instance(exception)

    def done(self) -> bool:
        return self._done

    def add_done_callback(self, callback) -> None:
        self._callbacks.append(callback)
        if self.done():
            self._schedule_callbacks()

    def __await__(self):
        yield self
        return self.result()

    def _schedule_callbacks(self):
        loop = _loop.get_event_loop()
        while self._callbacks:
            loop.call_soon(self._callbacks.popleft(), self)

    def _validate_not_done(self):
        if self.done():
            raise InvalidStateError(f'Future {self} is already done')

    def _validate_done(self):
        if not self.done():
            raise InvalidStateError(f'Future {self} is not done')

    def _mark_as_done(self):
        self._done = True
        logger.debug('%s is done', self)

    @contextlib.contextmanager
    def _transition_to_done(self):
        self._validate_not_done()
        yield
        self._mark_as_done()
        self._schedule_callbacks()

    def __str__(self) -> str:
        state = self._get_done_state() if self.done() else 'pending'
        return f'<Future {state}>'

    def _has_failed(self) -> bool:
        assert self._done
        return self._result is _MISSING

    def _get_done_state(self) -> str:
        if self._has_failed():
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
