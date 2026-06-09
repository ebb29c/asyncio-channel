from __future__ import annotations

__all__ = ('wait_all', 'wait_first', 'set_exception_handler')

import logging
from asyncio import FIRST_COMPLETED, CancelledError, Task, create_task, wait
from collections.abc import Callable, Coroutine
from typing import Any

_logger = logging.getLogger(__name__)


def _default_exception_handler(exc: BaseException, task: Task[Any]) -> None:
    _logger.error(
        'Unhandled exception in background task %r', task, exc_info=exc,
    )


_exception_handler: Callable[[BaseException, Task[Any]], None] | None = (
    _default_exception_handler
)


def set_exception_handler(
        fn: Callable[[BaseException, Task[Any]], None] | None) -> None:
    """Register a callable invoked when a background task raises an exception.

    fn(exc, task) receives the exception and the asyncio.Task.  Pass None to
    suppress reporting entirely.  The default handler logs via the
    asyncio_channel._util logger.
    """
    global _exception_handler
    _exception_handler = fn


def _task_done_callback(task: Task[Any]) -> None:
    """Attached as a done-callback to background tasks that have no output
    channel to close on failure.  Forwards exceptions to the registered
    exception handler."""
    if not task.cancelled() and task.exception() is not None:
        handler = _exception_handler
        if handler is not None:
            handler(task.exception(), task)


async def wait_all(
        *coros_or_tasks: Coroutine[Any, Any, Any] | Task[Any],
        timeout: float | None = None,
        create_task: Callable[..., Task[Any]] = create_task,
) -> tuple[set[Task[Any]], set[Task[Any]]]:
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
        *coros_or_tasks: Coroutine[Any, Any, Any] | Task[Any],
        timeout: float | None = None,
        create_task: Callable[..., Task[Any]] = create_task,
) -> tuple[set[Task[Any]], set[Task[Any]]]:
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
            return_when=FIRST_COMPLETED)
    except CancelledError:
        for task in tasks:
            if not task.done():
                task.cancel()

        raise
    else:
        for task in pending:
            task.cancel()

        return done, pending
