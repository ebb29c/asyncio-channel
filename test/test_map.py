from asyncio_channel import create_channel, map

import asyncio
import operator


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

async def test_map_stops_when_out_closed():
    """
    GIVEN
        A map whose output channel is closed by the consumer.
    WHEN
        The input channel still holds items.
    EXPECT
        The background task stops draining the input channel.
    """
    src = create_channel(5)
    for i in range(5):
        assert src.offer(i)
    out = map(operator.neg, (src,), 1)
    assert await out.take(timeout=1.0) == 0
    out.close()
    # Let the background task observe the closed output and stop.
    for _ in range(10):
        await asyncio.sleep(0)
    # 0 was buffered on out; 1 was in flight when out closed.
    # 2, 3, and 4 must remain on src.
    assert src.poll() == 2
