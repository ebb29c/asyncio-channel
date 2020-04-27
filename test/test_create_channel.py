from asyncio_channel import create_sliding_buffer, create_channel
from asyncio_channel._channel import Channel

import asyncio
import pytest


def test_chan():
    """
    WHEN
        n is omitted.
    EXPECT
        Return a Channel.
    """
    assert isinstance(create_channel(), Channel)

def test_chan_int():
    """
    WHEN
        n is a positive integer.
    EXPECT
        Return a Channel.
    """
    assert isinstance(create_channel(2), Channel)

def test_chan_buffer():
    """
    WHEN
        n is a buffer.
    EXPECT
        Return a Channel.
    """
    buf = create_sliding_buffer(2)
    assert isinstance(create_channel(buf), Channel)

def test_chan_nonpositive_int():
    """
    WHEN
        n is not a positive integer.
    EXPECT
        Throws a ValueError.
    """
    with pytest.raises(ValueError):
        create_channel(0)

def test_chan_nonpositive_buffer():
    """
    WHEN
        n is buffer with a non-positive maxsize.
    EXPECT
        Throws a ValueError.
    """
    buf = asyncio.Queue()
    with pytest.raises(ValueError):
        create_channel(buf)

def test_chan_nonbuffer():
    """
    WHEN
        n is not an integer or a buffer-like object.
    EXPECT
        Throws an AttributeError.
    """
    with pytest.raises(AttributeError):
        create_channel('a')
