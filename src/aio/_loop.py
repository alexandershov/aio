import collections
import functools
import heapq
import inspect
import logging
import time
import typing as tp

logger = logging.getLogger(__name__)

_SOON_CALLBACK_PRIORITY = 0
_DELAYED_CALLBACK_PRIORITY = 1


@functools.total_ordering
class _Callback:
    def __init__(
            self,
            priority: int,
            when: float,
            index: int,
            function: tp.Callable,
            args: tp.Tuple) -> None:
        self._priority = priority
        self._when = when
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
            logger.debug('Skipping call of cancelled %s', self)
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
        return self._priority, self._when, self._index


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
        self._callbacks: tp.List[_Callback] = []
        self._callbacks_counter = 0
        self._running = False
        self._is_closed = False
        self._pending_callbacks: tp.Deque[_Callback] = collections.deque()
        self._current_task = None
        self._all_tasks = set()
        self._exception_handler = _default_exception_handler

    def call_soon(self, callback, *args) -> Handle:
        self._validate_is_not_closed()
        callback = _Callback(
            priority=_SOON_CALLBACK_PRIORITY,
            when=self.time(),
            index=self._callbacks_counter,
            function=callback,
            args=args)
        self._add_callback(callback)
        return Handle(callback)

    def call_later(self, delay, callback, *args) -> TimerHandle:
        self._validate_is_not_closed()
        when = self.time() + delay
        return self.call_at(when, callback, *args)

    def call_at(self, when, callback, *args) -> TimerHandle:
        self._validate_is_not_closed()
        callback = _Callback(
            priority=_DELAYED_CALLBACK_PRIORITY,
            when=when,
            index=self._callbacks_counter,
            function=callback,
            args=args)
        self._add_callback(callback)
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
            self._wait_for_next_callback()
            self._prepare_pending_callbacks()
            self._call_pending_callbacks()

    def _wait_for_next_callback(self):
        sleep_duration = self._get_time_till_next_callback()
        if sleep_duration:
            time.sleep(sleep_duration)

    def _prepare_pending_callbacks(self):
        assert not self._pending_callbacks
        now = self.time()
        while self._has_ready_callback(now):
            a_callback = heapq.heappop(self._callbacks)
            self._pending_callbacks.append(a_callback)

    def _call_pending_callbacks(self):
        while self._pending_callbacks:
            callback = self._pending_callbacks.popleft()
            # noinspection PyBroadException
            try:
                callback()
            except Exception as exc:
                context = {
                    'message': str(exc),
                    'exception': exc,
                }
                self._exception_handler(self, context)

    def run_until_complete(self, future):
        from . import _task
        self._validate_is_not_closed()
        logger.debug('Running %s until %s is complete', self, future)
        future = _task.ensure_future(future)
        future.add_done_callback(lambda _: self.stop())

        self.run_forever()

        if not future.done():
            raise RuntimeError(f'Loop stopped before {future} completed')
        return future.result()

    def close(self):
        if self.is_running():
            raise RuntimeError('Event loop is running')
        self._is_closed = True

    def is_closed(self) -> bool:
        return self._is_closed

    def set_exception_handler(self, exception_handler):
        self._exception_handler = exception_handler

    def current_task(self):
        return self._current_task

    def set_current_task(self, task):
        self._current_task = task

    def all_tasks(self):
        return self._all_tasks

    def add_task(self, task):
        self._all_tasks.add(task)
        task.add_done_callback(lambda _: self._all_tasks.remove(task))

    def _validate_is_not_closed(self):
        if self.is_closed():
            raise RuntimeError('Event loop is closed')

    def _has_ready_callback(self, now: float) -> bool:
        if not self._callbacks:
            return False
        return self._callbacks[0].when <= now

    def _get_time_till_next_callback(self):
        if not self._callbacks:
            return 1.0
        return max(0.0, self._callbacks[0].when - self.time())

    def _add_callback(self, callback: _Callback) -> None:
        logger.debug('Adding %s to %s', callback, self)
        heapq.heappush(self._callbacks, callback)
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
        loop.close()
        set_event_loop(None)


def _default_exception_handler(loop, context: dict) -> None:
    del loop  # unused
    logger.error('Got an exception: %s', context['message'], exc_info=True)
