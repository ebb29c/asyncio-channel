__all__ = ('wait_all', 'wait_first', 'set_exception_handler')

import logging
from asyncio import FIRST_COMPLETED, CancelledError, Task, create_task, wait

_logger = logging.getLogger(__name__)


def _default_exception_handler(exc, task):
    _logger.error(
        'Unhandled exception in background task %r', task, exc_info=exc,
    )


_exception_handler = _default_exception_handler


def set_exception_handler(fn):
    """Register a callable invoked when a background task raises an exception.

    fn(exc, task) receives the exception and the asyncio.Task.  Pass None to
    suppress reporting entirely.  The default handler logs via the
    asyncio_channel._util logger.
    """
    global _exception_handler
    _exception_handler = fn


def _task_done_callback(task):
    """Attached as a done-callback to background tasks that have no output
    channel to close on failure.  Forwards exceptions to the registered
    exception handler."""
    if not task.cancelled() and task.exception() is not None:
        handler = _exception_handler
        if handler is not None:
            handler(task.exception(), task)


async def wait_all(
        *coros_or_tasks,
        timeout=None,
        create_task=create_task,
        wait=wait,
        CancelledError=CancelledError,
        Task=Task):
    """Wait for all tasks to complete.

    Returns two tuples: completed tasks, pending tasks.  If timeout is
    provided then completed tasks set may be empty.
    """
    tasks = tuple(
        ct if isinstance(ct, Task) else create_task(ct)
        for ct in coros_or_tasks)

    try:
        done, pending = await wait(tasks, timeout=timeout)
    except CancelledError:
        for task in tasks:
            if not task.done():
                task.cancel()

        raise
    else:
        for task in pending:
            task.cancel()

        return done, pending


async def wait_first(
        *coros_or_tasks,
        timeout=None,
        wait=wait,
        return_when=FIRST_COMPLETED,
        CancelledError=CancelledError):
    """Wait for first task to complete.

    Returns two tuples: completed tasks, pending tasks.  If timeout is
    provided then completed tasks set may be empty.
    """
    tasks = tuple(
        ct if isinstance(ct, Task) else create_task(ct)
        for ct in coros_or_tasks)

    try:
        done, pending = await wait(
            tasks,
            timeout=timeout,
            return_when=return_when)
    except CancelledError:
        for task in tasks:
            if not task.done():
                task.cancel()

        raise
    else:
        for task in pending:
            task.cancel()

        return done, pending
