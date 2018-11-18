import collections
import functools
import heapq
import inspect
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


class TimerHandle(Handle):
    def when(self) -> float:
        return self._callback.when


class Loop:
    def __init__(self):
        self._running = False
        self._is_closed = False
        self._pending_callbacks: tp.Deque[_Callback] = collections.deque()
        # TODO: can _soon_callbacks and _delayed_callbacks be merged into a single attribute?
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

    def call_later(self, delay, callback, *args) -> TimerHandle:
        when = self.time() + delay
        return self.call_at(when, callback, *args)

    def call_at(self, when, callback, *args) -> TimerHandle:
        callback = _Callback(
            when=when,
            index=self._callbacks_counter,
            function=callback,
            args=args)
        self._add_delayed_callback(callback)
        return TimerHandle(callback)

    # noinspection PyMethodMayBeStatic
    def time(self) -> float:
        return time.monotonic()

    def stop(self) -> None:
        logger.debug('Stopping %s', self)
        self._call_pending_callbacks()
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def run_forever(self) -> None:
        self._validate_is_not_closed()
        logger.debug('Running %s forever', self)
        self._running = True
        while self._running:
            if not self._has_callbacks():
                time.sleep(1)
            else:
                self._prepare_pending_callbacks()
                self._call_pending_callbacks()
                # TODO: add sleep

    def _prepare_pending_callbacks(self):
        assert not self._pending_callbacks
        self._prepare_soon_pending_callbacks()
        self._prepared_delayed_pending_callbacks()

    def _call_pending_callbacks(self):
        while self._pending_callbacks:
            callback = self._pending_callbacks.popleft()
            # noinspection PyBroadException
            try:
                callback()
            except Exception:
                self._handle_callback_exception(callback)

    def run_until_complete(self, future):
        logger.debug('Running %s until %s is complete', self, future)
        future = aio.ensure_future(future)
        future.add_done_callback(lambda _: self.stop())

        self.run_forever()

        if not future.done():
            raise RuntimeError(f'Loop stopped before {future} completed')
        return future.result()

    def close(self):
        self._is_closed = True

    def is_closed(self) -> bool:
        return self._is_closed

    def _validate_is_not_closed(self):
        if self.is_closed():
            raise RuntimeError('Can\'t run closed loop')

    def _prepare_soon_pending_callbacks(self):
        self._pending_callbacks.extend(self._soon_callbacks)
        self._soon_callbacks = []

    def _prepared_delayed_pending_callbacks(self):
        now = self.time()
        while self._has_delayed_callback_to_call(now):
            a_callback = heapq.heappop(self._delayed_callbacks)
            self._pending_callbacks.append(a_callback)

    def _has_delayed_callback_to_call(self, now: float) -> bool:
        if not self._delayed_callbacks:
            return False
        return self._delayed_callbacks[0].when <= now

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


_MISSING = object()
_loop: Loop = _MISSING


def get_event_loop() -> Loop:
    if _loop is None:
        raise RuntimeError('Event loop is unset for this context')
    if _loop is _MISSING:
        set_event_loop(new_event_loop())
    return _loop


def new_event_loop() -> Loop:
    return Loop()


def set_event_loop(loop: tp.Optional[Loop]) -> None:
    global _loop
    _loop = loop


def get_running_loop() -> Loop:
    if (_loop is None) or (_loop is _MISSING):
        raise RuntimeError('No running loop')
    if not _loop.is_running():
        raise RuntimeError('No running loop')
    return _loop


def run(coro):
    if not inspect.iscoroutine(coro):
        raise ValueError(f'{coro!r} is not a coroutine')
    loop = new_event_loop()
    set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        # TODO: close loop
        set_event_loop(None)
