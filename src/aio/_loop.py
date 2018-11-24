import collections
import heapq
import inspect
import logging
import time
import typing as tp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_SOON_CALLBACK_LEVEL = 0
_DELAYED_CALLBACK_LEVEL = 1

_MISSING = object()


@dataclass(frozen=True, order=True)
class _Priority:
    level: int
    when: float
    index: int


class _Callback:
    def __init__(
            self,
            function: tp.Callable,
            args: tp.Tuple) -> None:
        self._function = function
        self._args = args
        self._cancelled = False

    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        logger.debug('Cancelling %s', self)
        self._cancelled = True

    def __call__(self):
        if self.cancelled():
            logger.debug('Skipping call of cancelled %s', self)
        else:
            return self._function(*self._args)

    def __repr__(self) -> str:
        return f'_Callback(function={self._function}, args={self._args})'


_Queue = tp.List[tp.Tuple[_Priority, _Callback]]


class Handle:
    def __init__(self, callback: _Callback) -> None:
        self._callback = callback

    def cancel(self) -> None:
        self._callback.cancel()

    def cancelled(self) -> bool:
        return self._callback.cancelled()


class TimerHandle(Handle):
    def __init__(self, callback: _Callback, when: float) -> None:
        super().__init__(callback)
        self._when = when

    def when(self) -> float:
        return self._when


class Loop:
    def __init__(self):
        self._queue: _Queue = []
        self._pending_callbacks: tp.Deque[_Callback] = collections.deque()
        self._callbacks_counter = 0

        self._is_running = False
        self._is_closed = False

        self._current_task = None
        self._all_tasks = set()

        self._exception_handler = _default_exception_handler

    def call_soon(self, callback, *args) -> Handle:
        self._require_not_is_closed()
        priority = self._build_soon_priority()
        callback = _Callback(callback, args)
        self._add_callback(priority, callback)
        return Handle(callback)

    def call_later(self, delay, callback, *args) -> TimerHandle:
        self._require_not_is_closed()
        when = self.time() + delay
        return self.call_at(when, callback, *args)

    def call_at(self, when, callback, *args) -> TimerHandle:
        self._require_not_is_closed()
        priority = self._build_delayed_priority(when)
        callback = _Callback(callback, args)
        self._add_callback(priority, callback)
        return TimerHandle(callback, priority.when)

    # noinspection PyMethodMayBeStatic
    def time(self) -> float:
        return time.monotonic()

    def stop(self) -> None:
        logger.debug('Stopping %s', self)
        self._call_pending_callbacks()
        self._is_running = False

    def is_running(self) -> bool:
        return self._is_running

    def run_forever(self) -> None:
        self._require_not_is_closed()
        logger.debug('Running %s forever', self)
        self._is_running = True
        while self._is_running:
            self._wait_for_next_callback()
            self._prepare_pending_callbacks()
            self._call_pending_callbacks()

    def run_until_complete(self, future):
        from . import _task
        self._require_not_is_closed()
        logger.debug('Running %s until %s is complete', self, future)
        future = _task.ensure_future(future)
        future.add_done_callback(lambda _: self.stop())

        self.run_forever()

        if not future.done():
            raise RuntimeError(f'Loop stopped before {future} completed')
        return future.result()

    def close(self):
        self._require_not_is_running()
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

    def _require_not_is_running(self):
        if self.is_running():
            raise RuntimeError('Event loop is running')

    def _build_soon_priority(self) -> _Priority:
        return _Priority(
            level=_SOON_CALLBACK_LEVEL,
            when=self.time(),
            index=self._callbacks_counter)

    def _build_delayed_priority(self, when: float) -> _Priority:
        return _Priority(
            level=_DELAYED_CALLBACK_LEVEL,
            when=when,
            index=self._callbacks_counter)

    def _wait_for_next_callback(self):
        pause = self._get_pause_till_next_callback()
        if pause > 0:
            time.sleep(pause)

    def _prepare_pending_callbacks(self):
        assert not self._pending_callbacks
        now = self.time()
        while self._has_ready_callback(now):
            callback = self._pop_ready_callback()
            self._pending_callbacks.append(callback)

    def _pop_ready_callback(self) -> _Callback:
        _, callback = heapq.heappop(self._queue)
        return callback

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

    def _require_not_is_closed(self):
        if self.is_closed():
            raise RuntimeError('Event loop is closed')

    def _has_ready_callback(self, now: float) -> bool:
        if not self._queue:
            return False
        return self._get_when_of_next_callback() <= now

    def _get_pause_till_next_callback(self):
        if not self._queue:
            return 1.0
        return max(0.0, self._get_when_of_next_callback() - self.time())

    def _get_when_of_next_callback(self):
        priority, _ = self._queue[0]
        return priority.when

    def _add_callback(self, priority: _Priority, callback: _Callback) -> None:
        logger.debug('Adding %s to %s', callback, self)
        heapq.heappush(self._queue, (priority, callback))
        self._callbacks_counter += 1

    def __str__(self):
        state = 'running' if self._is_running else 'pending'
        return f'<Loop {state}>'


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
