from asyncio_channel import create_channel, split

import asyncio
import pytest


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
    await asyncio.wait_for(t_out.closed(), timeout=1.0)
    await asyncio.wait_for(f_out.closed(), timeout=1.0)

async def test_split_stops_when_both_outs_closed():
    """
    GIVEN
        A split whose output channels are both closed by consumers.
    WHEN
        The input channel still holds items.
    EXPECT
        The background task stops draining the input channel.
    """
    src = create_channel(5)
    for i in (1, 2, 3, 4, 5):
        assert src.offer(i)
    is_even = lambda n: n % 2 == 0
    evens, odds = split(is_even, src, 1, 1)
    evens.close()
    odds.close()
    # Let the background task observe the closed outputs and stop.
    for _ in range(10):
        await asyncio.sleep(0)
    # At most the in-flight items are consumed; the tail must remain.
    assert not src.empty()
