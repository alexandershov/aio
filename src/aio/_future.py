class Future:
    def __init__(self):
        self._result = None

    def result(self):
        return self._result

    def set_result(self, result):
        self._result = result
