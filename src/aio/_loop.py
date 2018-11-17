import functools
import heapq
import logging
import time
import typing as tp

import aio

logger = logging.getLogger(__name__)


@functools.total_ordering
class _Callback:
    # noinspection PyShadowingBuiltins
    def __init__(
            self,
            when: float,
            index: int,
            function: tp.Callable,
            args: tp.Tuple) -> None:
        self._when = when
        # TODO: remove index
        self._index = index
        self._function = function
        self._args = args
        self._cancelled = False

    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def when(self) -> float:
        return self._when

    def cancel(self) -> None:
        self._cancelled = True

    def __call__(self):
        if self.cancelled():
            logger.debug('%s is cancelled, skipping', self)
        else:
            return self._function(*self._args)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Callback):
            return NotImplemented
        return self._as_tuple() == other._as_tuple()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, _Callback):
            return NotImplemented
        return self._as_tuple() < other._as_tuple()

    def __repr__(self) -> str:
        return f'_Callback(when={self._when}, function={self._function}, args={self._args})'

    def _as_tuple(self):
        return self._when, self._index


class Handle:
    def __init__(self, callback: _Callback) -> None:
        self._callback = callback

    def cancel(self) -> None:
        self._callback.cancel()

    def cancelled(self) -> bool:
        return self._callback.cancelled()

    def when(self) -> float:
        return self._callback.when


class Loop:
    def __init__(self):
        self._running = False
        self._soon_callbacks: tp.List[_Callback] = []
        self._delayed_callbacks: tp.List[_Callback] = []
        self._callbacks_counter = 0

    def call_soon(self, callback, *args) -> Handle:
        callback = _Callback(
            when=self.time(),
            index=self._callbacks_counter,
            function=callback,
            args=args)
        self._add_soon_callback(callback)
        return Handle(callback)

    def call_later(self, delay, callback, *args) -> Handle:
        when = self.time() + delay
        return self.call_at(when, callback, *args)

    # TODO: return TimerHandle
    def call_at(self, when, callback, *args) -> Handle:
        callback = _Callback(
            when=when,
            index=self._callbacks_counter,
            function=callback,
            args=args)
        self._add_delayed_callback(callback)
        return Handle(callback)

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
            if not self._has_callbacks():
                time.sleep(1)
            else:
                self._call_soon_callbacks()
                self._call_delayed_callbacks()
                # TODO: add sleep

    def run_until_complete(self, future):
        logger.debug('Running %s until %s is complete', self, future)
        future = aio.ensure_future(future)
        future.add_done_callback(lambda _: self.stop())

        self.run_forever()

        if not future.done():
            raise RuntimeError(f'Loop stopped before {future} completed')
        return future.result()

    def _call_soon_callbacks(self):
        callbacks = self._soon_callbacks
        self._soon_callbacks = []
        self._call_callbacks(callbacks)

    def _call_delayed_callbacks(self):
        now = self.time()
        callbacks = []
        while True:
            if not self._delayed_callbacks:
                break
            if self._delayed_callbacks[0].when > now:
                break
            a_callback = heapq.heappop(self._delayed_callbacks)
            callbacks.append(a_callback)
        self._call_callbacks(callbacks)

    def _call_callbacks(self, callbacks: tp.Iterable[_Callback]) -> None:
        for a_callback in callbacks:
            # noinspection PyBroadException
            try:
                a_callback()
            except Exception:
                self._handle_callback_exception(a_callback)

    def _has_callbacks(self) -> bool:
        return bool(self._soon_callbacks or self._delayed_callbacks)

    # noinspection PyMethodMayBeStatic
    def _handle_callback_exception(self, callback: _Callback) -> None:
        logger.error('Got an exception during handling of %s: ', callback, exc_info=True)

    def _add_soon_callback(self, callback: _Callback) -> None:
        logger.debug('Adding %s to %s', callback, self)
        self._soon_callbacks.append(callback)
        self._callbacks_counter += 1

    def _add_delayed_callback(self, callback: _Callback) -> None:
        logger.debug('Adding %s to %s', callback, self)
        heapq.heappush(self._delayed_callbacks, callback)
        self._callbacks_counter += 1

    def __str__(self):
        state = 'running' if self._running else 'pending'
        return f'<Loop {state}>'


_loop = Loop()


def get_event_loop() -> Loop:
    return _loop
