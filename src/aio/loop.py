import collections


class Loop:
    def __init__(self):
        self._running = False
        self._callbacks = collections.deque()

    def call_soon(self, callback):
        self._callbacks.append(callback)

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def run_forever(self) -> None:
        self._running = True
        while self._callbacks:
            callback = self._callbacks.popleft()
            callback()


def get_event_loop() -> Loop:
    return Loop()
