from ._errors import CancelledError, InvalidStateError

from ._future import Future

from ._loop import (
    Loop,
    get_event_loop, get_running_loop, new_event_loop, set_event_loop,
    run)

from ._task import Task, ensure_future, current_task, all_tasks


def _configure_logging():
    import logging
    logging.getLogger(__name__).addHandler(logging.NullHandler())


_configure_logging()
