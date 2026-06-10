from __future__ import annotations

__all__ = ('map',)

from asyncio import Task, create_task
from collections.abc import Callable, Coroutine, Iterable
from typing import Any

from ._channel import Channel
from ._create_channel import create_channel
from ._iter import iterzip
from ._types import BufferProtocol, ReadableChannel
from ._util import _task_done_callback


async def _map(fn: Callable[..., Any], chs: Iterable[ReadableChannel],
               out: Channel, iterzip: Callable[..., Any] = iterzip) -> None:
    try:
        async for items in iterzip(*chs):
            x = fn(*items)
            await out.put(x)
        out.close()
    except Exception:
        out.close()
        raise


def map(fn: Callable[..., Any], chs: Iterable[ReadableChannel],
        buffer: int | BufferProtocol = 1, *,
        _create_channel: Callable[[int | BufferProtocol], Channel] = create_channel,
        _create_task: Callable[..., Task[Any]] = create_task,
        _map: Callable[..., Coroutine[Any, Any, None]] = _map,
        _task_done_callback: Callable[[Task[Any]], None] = _task_done_callback,
        ) -> Channel:
    """Get a channel with mapped values.

    fn is applied to each set of items taken from all input channels.
    The result is put on the output channel.

    The output channel will be closed when any of the input channels
    is closed.
    """
    out = _create_channel(buffer)
    task = _create_task(_map(fn, chs, out))
    task.add_done_callback(_task_done_callback)
    return out
