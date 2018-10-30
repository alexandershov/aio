import contextlib


class InvalidStateError(Exception):
    pass


_MISSING = object()


class Future:
    def __init__(self):
        self._result = _MISSING
        self._exception = _MISSING
        self._done = False

    def result(self):
        self._validate_done()
        if self._result is _MISSING:
            raise self._exception
        return self._result

    def set_result(self, result):
        with self._transition_to_done():
            self._result = result
            self._exception = None

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

    def done(self):
        return self._done

    def _validate_not_done(self):
        if self.done():
            raise InvalidStateError(f'Future {self} is already done')

    def _validate_done(self):
        if not self.done():
            raise InvalidStateError(f'Future {self} is not done')

    def _mark_as_done(self):
        self._done = True

    @staticmethod
    def _validate_exception(value):
        if not Future._is_exception(value):
            raise TypeError

    @staticmethod
    def _is_exception(value):
        if isinstance(value, Exception):
            return True
        if isinstance(value, type) and issubclass(value, Exception):
            return True
        return False

    @contextlib.contextmanager
    def _transition_to_done(self):
        self._validate_not_done()
        yield
        self._mark_as_done()
