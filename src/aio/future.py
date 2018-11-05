import collections
import contextlib

from . import _loop


class InvalidStateError(Exception):
    pass


_MISSING = object()


class Future:
    def __init__(self):
        self._result = _MISSING
        self._exception = _MISSING
        self._done = False
        self._callbacks = collections.deque()

    def result(self):
        self._validate_done()
        if self._result is _MISSING:
            raise self._exception
        return self._result

    def set_result(self, result):
        with self._transition_to_done():
            self._result = result
            self._exception = None
        self._schedule_callbacks()

    def exception(self):
        self._validate_done()
        return self._exception

    def set_exception(self, exception):
        with self._transition_to_done():
            if isinstance(exception, Exception):
                self._exception = exception
            elif isinstance(exception, type) and issubclass(exception, Exception):
                self._exception = exception()
            else:
                raise TypeError(f'{exception!r} is not an exception')
        self._schedule_callbacks()

    def done(self):
        return self._done

    def add_done_callback(self, callback):
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
