class InvalidStateError(Exception):
    pass


_MISSING = object()


class Future:
    def __init__(self):
        self._result = _MISSING

    def result(self):
        return self._result

    def set_result(self, result):
        if self._result is not _MISSING:
            raise InvalidStateError(f'Future {self} already has result {self._result}')
        self._result = result
