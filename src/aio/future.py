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
        if self._exception is not _MISSING:
            raise self._exception
        return self._result

    def set_result(self, result):
        self._validate_not_done()
        self._done = True
        self._result = result

    def done(self):
        return self._done

    def exception(self):
        self._validate_done()
        return self._exception

    def set_exception(self, exception):
        self._validate_not_done()
        self._done = True
        if isinstance(exception, type):
            self._exception = exception()
        else:
            self._exception = exception

    def _validate_not_done(self):
        if self.done():
            raise InvalidStateError(f'Future {self} is already done')

    def _validate_done(self):
        if not self.done():
            raise InvalidStateError(f'Future {self} is not done')
