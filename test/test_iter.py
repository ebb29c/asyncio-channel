from asyncio_channel import create_channel, itermerge, iterzip

import asyncio
import itertools
import pytest
import random

@pytest.mark.asyncio
async def test_itermerge():
    """
    GIVEN
        Multiple input channels.
    WHEN
        Items put to each input channels.
    EXPECT
        An iteration when an item is on any channel.
    """
    async def put(seq, *chs):
        for x, ch in zip(seq, itertools.cycle(chs)):
            await ch.put(x)
            await asyncio.sleep(0.1 * random.random())
        chs[0].close()

    ch1 = create_channel()
    ch2 = create_channel()
    ch3 = create_channel()
    seq = ('a', 1, 'x', 'b', 2, 'y', 'c', 3, 'z')
    asyncio.create_task(put(seq, ch1, ch2, ch3))
    results = []
    async for x in itermerge(ch1, ch2, ch3):
        results.append(x)
    assert tuple(results) == seq

@pytest.mark.asyncio
async def test_iterzip():
    """
    GIVEN
        Multiple input channels.
    WHEN
        Iterate over zip of channels.
    EXPECT
        An iteration when all channels have an item.
    """
    async def put_seq(seq, ch):
        for x in seq:
            await asyncio.sleep(0.1 * random.random())
            await ch.put(x)

    ch1 = create_channel()
    ch2 = create_channel()
    ch3 = create_channel()
    seq1 = ('a', 'b', 'c')
    seq2 = (1, 2, 3)
    seq3 = ('x', 'y', 'z')
    asyncio.create_task(put_seq(seq1, ch1))
    asyncio.create_task(put_seq(seq2, ch2))
    asyncio.create_task(put_seq(seq3, ch3))
    i = 0
    async for zs in iterzip(ch1, ch2, ch3):
        assert zs == (seq1[i], seq2[i], seq3[i])
        i += 1
        if i == len(seq2):
            ch2.close()
    await asyncio.sleep(0.05)
