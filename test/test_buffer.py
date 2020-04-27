from asyncio_channel._buffer import create_blocking_buffer

import asyncio
import pytest


def test_blocking_buffer():
    """
    WHEN
        n is a positive integer.
    EXPECT
        Returns an asyncio.Queue.
    """
    assert isinstance(create_blocking_buffer(1), asyncio.Queue)

def test_blocking_buffer_not_int():
    """
    WHEN
        n is not an integer.
    EXPECT
        Throws a TypeError.
    """
    with pytest.raises(TypeError):
        create_blocking_buffer('a')

def test_blocking_buffer_nonpositive_int():
    """
    WHEN
        n is a non-positive integer.
    EXPECT
        Throws a ValueError.
    """
    with pytest.raises(ValueError):
        create_blocking_buffer(0)
