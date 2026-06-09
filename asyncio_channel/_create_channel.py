from __future__ import annotations

__all__ = ('create_channel',)

from ._buffer import create_blocking_buffer
from ._channel import Channel
from ._types import BufferProtocol


def create_channel(buffer: int | BufferProtocol = 1) -> Channel:
    """Create a new channel.

    As a conveinence, if buffer is a positive integer then creates a
    blocking buffer for the new channel.
    """
    buf = buffer
    if isinstance(buffer, int):
        buf = create_blocking_buffer(buffer)
    elif buf.maxsize < 1:
        raise ValueError('buffer maxsize must be a positive integer')
    return Channel(buf)
