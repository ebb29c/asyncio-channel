__all__ = ('create_channel',)

from ._buffer import create_blocking_buffer
from ._channel import Channel


def create_channel(n_or_buffer=1):
    """Create a new channel.

    As a conveinence, if n_or_buffer is a positive integer then creates a
    blocking buffer for the new channel.
    """
    buf = n_or_buffer
    if isinstance(n_or_buffer, int):
        buf = create_blocking_buffer(n_or_buffer)
    elif buf.maxsize < 1:
        raise ValueError(f'buffer maxsize must be a positive integer')
    return Channel(buf)
