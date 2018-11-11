import collections
import contextlib

from . import _loop


class BaseError(Exception):
    pass


class InvalidStateError(BaseError):
    pass


_MISSING = object()


class Future:
    def __init__(self):
        self._result = _MISSING
        self._exception: Exception = _MISSING
        self._done = False
        self._callbacks = collections.deque()

    def result(self) -> object:
        self._validate_done()
        if self._result is _MISSING:
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

    @contextlib.contextmanager
    def _transition_to_done(self):
        self._validate_not_done()
        yield
        self._mark_as_done()
        self._schedule_callbacks()


def _build_exception_instance(exception) -> Exception:
    if isinstance(exception, Exception):
        return exception
    if _is_subclass_of_exception(exception):
        return exception()
    raise TypeError(f'{exception!r} is not an exception')


def _is_subclass_of_exception(exception) -> bool:
    return isinstance(exception, type) and issubclass(exception, Exception)
