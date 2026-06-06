__all__ = ('onto_channel', 'to_channel')

from asyncio import create_task

from ._create_channel import create_channel
from ._util import _task_done_callback


async def _onto_channel(coll, dest, done, close):
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


def onto_channel(collection, ch, *, close=True,
                 _create_channel=create_channel, _create_task=create_task,
                 _onto_channel=_onto_channel,
                 _task_done_callback=_task_done_callback):
    """Copy items from collection to channel.

    If "close" is True then channel will be closed when done.

    Returns a new channel that will be closed after all items have been
    copied.
    """
    done = _create_channel()
    task = _create_task(_onto_channel(collection, ch, done, close))
    task.add_done_callback(_task_done_callback)
    return done


def to_channel(collection, *,
               _create_channel=create_channel, _onto_channel=onto_channel):
    """Copy items from collection to a new channel.

    Returns a new channel that will be closed after all items have been
    copied.
    """
    out = _create_channel()
    _onto_channel(collection, out)
    return out
