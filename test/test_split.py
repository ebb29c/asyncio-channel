from asyncio_channel import create_channel, split

import asyncio
import pytest


@pytest.mark.asyncio
async def test_split():
    """
    GIVEN
        An input channel and predicate, is_even.
    WHEN
        A number if put on the input channel.
    EXPECT
        Even number put on the true channel, odd numbe on the
        false channel.
    """
    is_even = lambda n: n % 2 == 0
    ch = create_channel()
    t_out, f_out = split(is_even, ch)
    x = 2
    assert ch.offer(x)
    r = await t_out.take(timeout=0.05)
    assert x == r
    assert f_out.empty()
    x = 3
    assert ch.offer(x)
    r = await f_out.take(timeout=0.05)
    assert x == r
    assert t_out.empty()
    ch.close()
    await asyncio.wait_for(
        asyncio.wait((t_out.closed(), f_out.closed())),
        timeout=0.05)
