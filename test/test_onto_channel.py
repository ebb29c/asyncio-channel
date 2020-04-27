from asyncio_channel import create_channel, onto_channel, to_channel

import asyncio
import pytest


@pytest.mark.asyncio
async def test_onto_channel():
    """
    WHEN
        Called with a collection and a channel.
    EXPECT
        All items to be put on channel and then closed.
    """
    coll = (1, 2, 3)
    ch = create_channel()
    done = onto_channel(coll, ch)
    taken = []
    async for x in ch:
        taken.append(x)
    await asyncio.wait_for(done.closed(), timeout=0.05)
    assert tuple(taken) == coll
    assert ch.is_closed()

@pytest.mark.asyncio
async def test_onto_channel_close_false():
    """
    WHEN
        Called with a collection, a channel, and close=False.
    EXPECT
        All items to be put on channel, but channel is not closed.
    """
    coll = (1, 2, 3)
    ch = create_channel(len(coll))
    done = onto_channel(coll, ch, close=False)
    await asyncio.wait_for(done.closed(), timeout=0.05)
    assert not ch.is_closed()
    for n in coll:
        assert ch.poll() == n
    assert ch.empty()
    ch.close()
    await asyncio.sleep(0.05)

@pytest.mark.asyncio
async def test_onto_channel_dest_closed():
    """
    WHEN
        Called with a collection and a closedchannel.
    EXPECT
        All items to be put on channel and then closed.
    """
    coll = (1, 2, 3)
    ch = create_channel()
    ch.close()
    out = onto_channel(coll, ch)
    await asyncio.wait_for(out.closed(), timeout=0.05)
    assert ch.empty()

@pytest.mark.asyncio
async def test_to_channel():
    """
    WHEN
        Called with a collection.
    EXPECT
        All items put on returned channel and then closed.
    """
    coll = (1, 2, 3)
    out = to_channel(coll)
    taken = []
    async for x in out:
        taken.append(x)
    assert tuple(taken) == coll
    assert out.is_closed()
