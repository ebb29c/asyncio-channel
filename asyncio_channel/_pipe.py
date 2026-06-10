from __future__ import annotations

__all__ = ('pipe',)

from asyncio import Task, create_task
from collections.abc import Callable, Coroutine
from typing import Any

from ._types import ReadableChannel, WritableChannel, _WaitFn
from ._util import _task_done_callback, wait_all


async def _pipe(src: ReadableChannel, dest: WritableChannel, close: bool,
                _wait_all: _WaitFn = wait_all) -> None:
    """Transfer items from src to dest."""
    try:
        while True:
            await _wait_all(src.item(), dest.capacity())

            if src.empty() or dest.is_closed():
                break
            if dest.full():
                # The capacity observed during the wait was consumed by
                # another producer before an item arrived; wait again
                # rather than dropping a polled item on a failed offer.
                continue

            x = src.poll()
            dest.offer(x)

        if close and src.is_closed():
            dest.close()
    except Exception:
        dest.close()
        raise


_PipeFn = Callable[[ReadableChannel, WritableChannel, bool], Coroutine[Any, Any, None]]


def pipe(src: ReadableChannel, dest: WritableChannel, *, close: bool = True,
         _create_task: Callable[..., Task[Any]] = create_task,
         _pipe: _PipeFn = _pipe,
         _task_done_callback: Callable[[Task[Any]], None] = _task_done_callback,
         ) -> None:
    """Transfer items from src to dest.

    When src is closed, and "close" is True, then dest will be closed.
    """
    task = _create_task(_pipe(src, dest, close))
    task.add_done_callback(_task_done_callback)
