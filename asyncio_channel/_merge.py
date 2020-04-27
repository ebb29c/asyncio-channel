__all__ = ('merge',)

from asyncio import create_task

from ._create_channel import create_channel
from ._iter import itermerge


async def _wait(chs, out, itermerge=itermerge):
    async for x in itermerge(*chs):
        await out.put(x)

    out.close()


def merge(chs, n_or_buffer=1, *,
          _create_channel=create_channel, _create_task=create_task,
          _wait=_wait):
    """Merge multiple channels into a single channel.

    Return a new channel, created with n_or_buffer.  Item put on the
    input channels will be taken and put on the output channel.

    The returned channel will be closed when all input channels are
    closed.
    """
    out = _create_channel(n_or_buffer)
    _create_task(_wait(chs, out))
    return out
