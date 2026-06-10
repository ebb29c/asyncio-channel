from __future__ import annotations

__all__ = ('merge',)

from asyncio import Task, create_task
from collections.abc import Callable, Coroutine, Iterable
from typing import Any

from ._channel import Channel
from ._create_channel import create_channel
from ._iter import itermerge
from ._types import BufferProtocol, ReadableChannel
from ._util import _task_done_callback


async def _wait(chs: Iterable[ReadableChannel], out: Channel,
                itermerge: Callable[..., Any] = itermerge) -> None:
    try:
        async for x in itermerge(*chs):
            await out.put(x)
        out.close()
    except Exception:
        out.close()
        raise


def merge(chs: Iterable[ReadableChannel], buffer: int | BufferProtocol = 1, *,
          _create_channel: Callable[[int | BufferProtocol], Channel] = create_channel,
          _create_task: Callable[..., Task[Any]] = create_task,
          _wait: Callable[..., Coroutine[Any, Any, None]] = _wait,
          _task_done_callback: Callable[[Task[Any]], None] = _task_done_callback,
          ) -> Channel:
    """Merge multiple channels into a single channel.

    Return a new channel, created with buffer.  Item put on the
    input channels will be taken and put on the output channel.

    The returned channel will be closed when all input channels are
    closed.
    """
    out = _create_channel(buffer)
    task = _create_task(_wait(chs, out))
    task.add_done_callback(_task_done_callback)
    return out
