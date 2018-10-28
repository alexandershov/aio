class InvalidStateError(Exception):
    pass


_MISSING = object()


class Future:
    def __init__(self):
        self._result = _MISSING
        self._exception = _MISSING
        self._done = False

    def result(self):
        if not self.done():
            raise InvalidStateError(f'Future {self} has no result')
        return self._result

    def set_result(self, result):
        if self.done():
            raise InvalidStateError(f'Future {self} is already done')
        self._done = True
        self._result = result

    def done(self):
        return self._done

    def exception(self):
        return self._exception

    def set_exception(self, exception):
        if self.done():
            raise InvalidStateError(f'Future {self} is already done')
        self._done = True
        if isinstance(exception, type):
            self._exception = exception()
        else:
            self._exception = exception
