__all__ = ('reduce',)

from asyncio import create_task

from ._create_channel import create_channel


async def _reduce(out, fn, ch, init):
    """Reduce items from channel."""
    acc = init
    async for x in ch:
        acc = fn(acc, x)

    await out.put(acc)
    out.close()


def reduce(fn, ch, init=None, *,
           _create_channel=create_channel, _create_task=create_task):
    """Reduce items taken from channel.

    Returns a new channel which will receive the result, or init if
    channel closes without yielding an item.

    fn will receive two arguments: init and the first item taken from
    channel, then that result and the second item taken from channel,
    and so on until the channel closes.  The final result will be put
    on the returned channel.
    """
    out = _create_channel()
    _create_task(_reduce(out, fn, ch, init))
    return out
