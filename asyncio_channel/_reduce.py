from __future__ import annotations

__all__ = ('reduce',)

from asyncio import Task, create_task
from collections.abc import Callable
from typing import Any

from ._channel import Channel
from ._create_channel import create_channel
from ._types import ReadableChannel
from ._util import _task_done_callback


async def _reduce(out: Channel, fn: Callable[[Any, Any], Any],
                  ch: ReadableChannel, init: Any) -> None:
    """Reduce items from channel."""
    try:
        acc = init
        async for x in ch:
            acc = fn(acc, x)
        await out.put(acc)
        out.close()
    except Exception:
        out.close()
        raise


def reduce(fn: Callable[[Any, Any], Any], ch: ReadableChannel,
           init: Any = None, *,
           _create_channel: Callable[[], Channel] = create_channel,
           _create_task: Callable[..., Task[Any]] = create_task,
           _task_done_callback: Callable[[Task[Any]], None] = _task_done_callback,
           ) -> Channel:
    """Reduce items taken from channel.

    Returns a new channel which will receive the result, or init if
    channel closes without yielding an item.

    fn will receive two arguments: init and the first item taken from
    channel, then that result and the second item taken from channel,
    and so on until the channel closes.  The final result will be put
    on the returned channel.
    """
    out = _create_channel()
    task = _create_task(_reduce(out, fn, ch, init))
    task.add_done_callback(_task_done_callback)
    return out
