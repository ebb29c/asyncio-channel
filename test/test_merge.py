from asyncio_channel import create_channel, merge

import asyncio


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

async def test_merge_stops_when_out_closed():
    """
    GIVEN
        A merge whose output channel is closed by the consumer.
    WHEN
        The input channel still holds items.
    EXPECT
        The background task stops draining the input channel.
    """
    src = create_channel(5)
    for x in 'abcde':
        assert src.offer(x)
    out = merge((src,), 1)
    assert await out.take(timeout=1.0) == 'a'
    out.close()
    # Let the background task observe the closed output and stop.
    for _ in range(10):
        await asyncio.sleep(0)
    # 'a' was buffered on out; 'b' was in flight when out closed.
    # 'c', 'd', and 'e' must remain on src.
    assert src.poll() == 'c'
