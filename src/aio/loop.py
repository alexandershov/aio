import heapq
import time
import typing as tp
from dataclasses import dataclass, field


class Loop:
    def __init__(self):
        self._running = False
        self._callbacks = []

    def call_soon(self, callback):
        return self.call_later(0, callback)

    def call_later(self, delay, callback):
        eta = time.monotonic() + delay
        heapq.heappush(self._callbacks, _ScheduledCallback(eta, callback))

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
                now = time.monotonic()
                if callback.eta > now:
                    time.sleep(callback.eta - now)
                else:
                    callback = heapq.heappop(self._callbacks)
                    callback.callback()


@dataclass(frozen=True, order=True)
class _ScheduledCallback:
    eta: float
    callback: tp.Callable = field(compare=False)


def get_event_loop() -> Loop:
    return Loop()
