from __future__ import annotations

__all__ = ('split',)

from asyncio import Task, create_task
from collections.abc import Callable, Coroutine
from typing import Any

from ._channel import Channel
from ._create_channel import create_channel
from ._types import BufferProtocol, ReadableChannel, WritableChannel
from ._util import _task_done_callback


async def _split(predicate: Callable[[Any], bool], ch: ReadableChannel,
                 true_out: WritableChannel, false_out: WritableChannel) -> None:
    """Sort items by predicate."""
    try:
        async for x in ch:
            out = true_out if predicate(x) else false_out
            await out.put(x)
        true_out.close()
        false_out.close()
    except Exception:
        true_out.close()
        false_out.close()
        raise


def split(predicate: Callable[[Any], bool], ch: ReadableChannel,
          true_buffer: int | BufferProtocol = 1,
          false_buffer: int | BufferProtocol = 1, *,
          _create_channel: Callable[[int | BufferProtocol], Channel] = create_channel,
          _create_task: Callable[..., Task[Any]] = create_task,
          _split: Callable[..., Coroutine[Any, Any, None]] = _split,
          _task_done_callback: Callable[[Task[Any]], None] = _task_done_callback,
          ) -> tuple[Channel, Channel]:
    """Sort channel items using predicate.

    Returns a tuple of two channels.  The first will contains items
    from input channel for which predicate returned True, other items
    will be put on the second channel.

    The output channels will be closed when the input channel is
    closed.
    """
    true_out = _create_channel(true_buffer)
    false_out = _create_channel(false_buffer)
    task = _create_task(_split(predicate, ch, true_out, false_out))
    task.add_done_callback(_task_done_callback)
    return true_out, false_out
