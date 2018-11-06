import heapq
import inspect
import time
import typing as tp
from dataclasses import dataclass, field

import aio


class Loop:
    def __init__(self):
        self._running = False
        self._callbacks = []
        self._num_callbacks = 0

    def call_soon(self, callback, *args):
        return self.call_later(0, callback, *args)

    def call_later(self, delay, callback, *args):
        eta = time.monotonic() + delay
        return self.call_at(eta, callback, *args)

    def call_at(self, eta, callback, *args):
        i = self._num_callbacks
        self._num_callbacks += 1
        heapq.heappush(self._callbacks, _ScheduledCallback(eta, i, callback, args))

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

    def run_until_complete(self, future):
        if inspect.iscoroutine(future):
            future = aio.Task(future)
        future.add_done_callback(lambda _: self.stop())
        self.run_forever()
        if not future.done():
            raise RuntimeError(f'Loop stopped before {future} completed')
        return future.result()


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
