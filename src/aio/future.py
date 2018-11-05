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
        self._callbacks = []

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
        _loop.get_event_loop().call_soon(self._schedule_callbacks)

    def done(self):
        return self._done

    # TODO: what should I do if this future is already done?
    def add_done_callback(self, callback):
        self._callbacks.append(callback)

    def __await__(self):
        yield self

    def _schedule_callbacks(self):
        # TODO: should I clear _callbacks here?
        loop = _loop.get_event_loop()
        for callback in self._callbacks:
            loop.call_soon(callback, self)

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
