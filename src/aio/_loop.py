import heapq
import inspect
import time
import typing as tp
from dataclasses import dataclass, field

import aio


class Loop:
    def __init__(self):
        self._running = False
        self._schedule = []
        self._callbacks_counter = 0

    def call_soon(self, callback, *args):
        return self.call_later(0, callback, *args)

    def call_later(self, delay, callback, *args):
        when = self.time() + delay
        return self.call_at(when, callback, *args)

    def call_at(self, when, callback, *args):
        scheduled_callback = _ScheduledCallback(
            when=when,
            index=self._callbacks_counter,
            fn=callback,
            args=args)
        heapq.heappush(self._schedule, scheduled_callback)
        self._callbacks_counter += 1

    def time(self) -> float:
        return time.monotonic()

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def run_forever(self) -> None:
        self._running = True
        while self._running:
            if not self._schedule:
                time.sleep(1)
            else:
                callback = self._schedule[0]
                now = self.time()
                if callback.when > now:
                    time.sleep(callback.when - now)
                else:
                    callback = heapq.heappop(self._schedule)
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
    when: float
    index: int

    fn: tp.Callable = field(compare=False)
    args: tp.Tuple = field(compare=False)

    def __call__(self):
        return self.fn(*self.args)


_loop = Loop()


def get_event_loop() -> Loop:
    return _loop
