_MISSING = object()


class Deferred:
    def __init__(self) -> None:
        self._result = _MISSING
        self._callbacks = []

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def callback(self, value):
        result = value
        for callback in self._callbacks:
            result = callback(result)
        self._result = result

    @property
    def result(self):
        if self._result_missing:
            raise ValueError(f'{self} has no result')
        return self._result

    @property
    def _result_missing(self) -> bool:
        return self._result is _MISSING

    def __repr__(self) -> str:
        if self._result_missing:
            return f'Deferred(result=Unknown)'
        return f'Deferred({self._result})'
