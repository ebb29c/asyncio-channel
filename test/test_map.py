from asyncio_channel import create_channel, map

import asyncio
import operator
import pytest


@pytest.mark.asyncio
async def test_map():
    """
    GIVEN
        Two input channels and operator.add.
    WHEN
        Two number are put on input channels.
    EXPECT
        Sum of the input number is put on output channel.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = map(operator.add, (ch1, ch2))
    a = 1
    b = 2
    assert ch1.offer(a)
    assert ch2.offer(b)
    x = await out.take(timeout=0.05)
    assert x == (a + b)
    ch1.close()
    await asyncio.wait_for(out.closed(), timeout=0.05)
