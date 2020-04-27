__all__ = ('split',)

from asyncio import create_task

from ._create_channel import create_channel


async def _split(predicate, ch, true_out, false_out):
    """Sort items by predicate."""
    async for x in ch:
        out = true_out if predicate(x) else false_out
        await out.put(x)

    true_out.close()
    false_out.close()


def split(predicate, ch, true_n_or_buffer=1, false_n_or_buffer=1, *,
          _create_channel=create_channel, _create_task=create_task,
          _split=_split):
    """Sort channel items using predicate.

    Returns a tuple of two channels.  The first will contains items
    from input channel for which predicate returned True, other items
    will be put on the second channel.

    The output channels will be closed when the input channel is
    closed.
    """
    true_out = _create_channel(true_n_or_buffer)
    false_out = _create_channel(false_n_or_buffer)
    _create_task(_split(predicate, ch, true_out, false_out))
    return true_out, false_out
