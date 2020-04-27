__all__ = ('map',)

from asyncio import create_task

from ._create_channel import create_channel
from ._iter import iterzip


async def _map(fn, chs, out, iterzip=iterzip):
    async for items in iterzip(*chs):
        x = fn(*items)
        await out.put(x)

    out.close()


def map(fn, chs, n_or_buffer=1, *,
        _create_channel=create_channel, _create_task=create_task,
        _map=_map):
    """Get a channel with mapped values.

    fn is applied to each set of items taken from all input channels.
    The result is put on the output channel.

    The output channel will be closed when any of the input channels
    is closed.
    """
    out = _create_channel(n_or_buffer)
    _create_task(_map(fn, chs, out))
    return out
