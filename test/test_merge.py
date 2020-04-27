from asyncio_channel import create_channel, merge

import asyncio
import pytest


@pytest.mark.asyncio
async def test_merge():
    """
    GIVEN
        Merge created with multiple input channels.
    WHEN
        Items put on input channels.
    EXPECT
        Items are taken from input channels and put on output channel.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = merge([ch1, ch2])
    a = 'a'
    b = 'b'
    ch1.offer(a)
    ch2.offer(b)
    x = await out.take(timeout=0.05)
    y = await out.take(timeout=0.05)
    assert not {x, y}.difference({a, b})
    ch1.close()
    ch2.close()
    await asyncio.wait_for(out.closed(), timeout=0.05)
