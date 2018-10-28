class InvalidStateError(Exception):
    pass


_MISSING = object()


class Future:
    def __init__(self):
        self._result = _MISSING
        self._exception = _MISSING

    def result(self):
        if not self.done():
            raise InvalidStateError(f'Future {self} has no result')
        return self._result

    def set_result(self, result):
        if self.done():
            raise InvalidStateError(f'Future {self} already has result {self._result}')
        self._result = result

    def done(self):
        return self._result is not _MISSING

    def exception(self):
        return self._exception

    def set_exception(self, exception):
        self._exception = exception
