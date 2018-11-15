import heapq
import logging
import time
import typing as tp
from dataclasses import dataclass, field

import aio

logger = logging.getLogger(__name__)


@dataclass(frozen=True, order=True)
class _Callback:
    when: float
    index: int

    callback: tp.Callable = field(compare=False)
    args: tp.Tuple = field(compare=False)

    def __call__(self):
        return self.callback(*self.args)


class Loop:
    def __init__(self):
        self._running = False
        self._callbacks = []
        self._callbacks_counter = 0

    def call_soon(self, callback, *args):
        return self.call_later(0, callback, *args)

    def call_later(self, delay, callback, *args):
        when = self.time() + delay
        return self.call_at(when, callback, *args)

    def call_at(self, when, callback, *args):
        callback = _Callback(
            when=when,
            index=self._callbacks_counter,
            callback=callback,
            args=args)
        self._add_callback(callback)

    # noinspection PyMethodMayBeStatic
    def time(self) -> float:
        return time.monotonic()

    def stop(self) -> None:
        logger.debug('Stopping %s', self)
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def run_forever(self) -> None:
        logger.debug('Running %s forever', self)
        self._running = True
        while self._running:
            if not self._callbacks:
                time.sleep(1)
            else:
                self._run_next_callback_or_wait()

    def run_until_complete(self, future):
        logger.debug('Running %s until %s is complete', self, future)
        future = aio.ensure_future(future)
        future.add_done_callback(lambda _: self.stop())

        self.run_forever()

        if not future.done():
            raise RuntimeError(f'Loop stopped before {future} completed')
        return future.result()

    def _run_next_callback_or_wait(self):
        callback = self._callbacks[0]
        now = self.time()
        if callback.when > now:
            time.sleep(callback.when - now)
        else:
            callback = heapq.heappop(self._callbacks)
            # noinspection PyBroadException
            try:
                callback()
            except Exception as exc:
                self._handle_callback_exception(callback, exc)

    def _handle_callback_exception(self, callback: _Callback, exc: Exception) -> None:
        logger.error('Got an exception during handling of %s: ', callback, exc_info=True)

    def _add_callback(self, callback: _Callback) -> None:
        logger.debug('Adding %s to %s', callback, self)
        heapq.heappush(self._callbacks, callback)
        self._callbacks_counter += 1

    def __str__(self):
        state = 'running' if self._running else 'pending'
        return f'<Loop {state}>'


_loop = Loop()


def get_event_loop() -> Loop:
    return _loop
