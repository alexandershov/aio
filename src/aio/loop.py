import heapq
import time
import typing as tp
from dataclasses import dataclass, field


class Loop:
    def __init__(self):
        self._running = False
        self._callbacks = []
        self._callbacks_count = 0

    def call_soon(self, fn, *args):
        return self.call_later(0, fn, *args)

    def call_later(self, delay, fn, *args):
        eta = time.monotonic() + delay
        return self.call_at(eta, fn, *args)

    def call_at(self, eta, fn, *args):
        i = self._callbacks_count
        self._callbacks_count += 1
        heapq.heappush(self._callbacks, _ScheduledCallback(eta, i, fn, args))

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
    args: tp.Tuple = field(compare=False)

    def __call__(self):
        return self.fn(*self.args)


_loop = Loop()


def get_event_loop() -> Loop:
    return _loop
