from __future__ import annotations

__all__ = ('onto_channel', 'to_channel')

from asyncio import Task, create_task
from collections.abc import Callable, Coroutine, Iterable
from typing import Any

from ._channel import Channel
from ._create_channel import create_channel
from ._types import WritableChannel
from ._util import _task_done_callback


async def _onto_channel(coll: Iterable[Any], dest: WritableChannel,
                        done: Channel, close: bool) -> None:
    """Copy items from src to dest channel."""
    try:
        for x in coll:
            if dest.is_closed():
                break
            await dest.put(x)
        if close:
            dest.close()
    except Exception:
        if close:
            dest.close()
        raise
    finally:
        done.close()  # Signal that all items have been copied (or failed).


_OntoChanFn = Callable[..., Coroutine[Any, Any, None]]


def onto_channel(collection: Iterable[Any], ch: WritableChannel, *,
                 close: bool = True,
                 _create_channel: Callable[[], Channel] = create_channel,
                 _create_task: Callable[..., Task[Any]] = create_task,
                 _onto_channel: _OntoChanFn = _onto_channel,
                 _task_done_callback: Callable[[Task[Any]], None] = _task_done_callback,
                 ) -> Channel:
    """Copy items from collection to channel.

    If "close" is True then channel will be closed when done.

    Returns a new channel that will be closed after all items have been
    copied.
    """
    done = _create_channel()
    task = _create_task(_onto_channel(collection, ch, done, close))
    task.add_done_callback(_task_done_callback)
    return done


def to_channel(collection: Iterable[Any], *,
               _create_channel: Callable[[], Channel] = create_channel,
               _onto_channel: Callable[..., Channel] = onto_channel,
               ) -> Channel:
    """Copy items from collection to a new channel.

    Returns a new channel that will be closed after all items have been
    copied.
    """
    out = _create_channel()
    _onto_channel(collection, out)
    return out
