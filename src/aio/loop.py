import heapq
import time
import typing as tp
from dataclasses import dataclass, field


class Loop:
    def __init__(self):
        self._running = False
        self._callbacks = []
        self._callbacks_count = 0

    def call_soon(self, fn):
        return self.call_later(0, fn)

    def call_later(self, delay, fn):
        eta = time.monotonic() + delay
        return self.call_at(eta, fn)

    def call_at(self, eta, fn):
        i = self._callbacks_count
        self._callbacks_count += 1
        heapq.heappush(self._callbacks, _ScheduledCallback(eta, i, fn))

    def time(self) -> float:
        return time.monotonic()

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def run_forever(self) -> None:
        self._running = True
        while self._running:
            if not self._callbacks:
                time.sleep(1)
            else:
                callback = self._callbacks[0]
                now = self.time()
                if callback.eta > now:
                    time.sleep(callback.eta - now)
                else:
                    callback = heapq.heappop(self._callbacks)
                    callback()


@dataclass(frozen=True, order=True)
class _ScheduledCallback:
    eta: float
    index: int
    fn: tp.Callable = field(compare=False)

    def __call__(self):
        return self.fn()


_loop = Loop()


def get_event_loop() -> Loop:
    return _loop
