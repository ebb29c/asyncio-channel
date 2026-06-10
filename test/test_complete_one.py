from asyncio_channel import complete_one, create_channel, shield_from_close

import asyncio
import pytest


async def test_alts_ready_take():
    """
    WHEN
        A ready "take" operation.
    EXPECT
        Return taken value and channel.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    x = 'x'
    ch2.offer(x)
    out = await asyncio.wait_for(complete_one(ch1, ch2), timeout=0.05)
    assert out == (x, ch2)

async def tests_alts_ready_put():
    """
    WHEN
        A ready "put" operation.
    EXPECT
        Return success and channel.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    a = 'a'
    ch1.offer(a)
    b, c = 'b', 'c'
    out = await asyncio.wait_for(complete_one((ch1, b), (ch2, c)), timeout=0.05)
    assert out == (True, ch2)
    assert ch1.poll() == a
    assert ch2.poll() == c

async def test_alts_default():
    """
    WHEN
        No ready ports and a default value.
    EXPECT
        Immediately return default.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    x = 'x'
    out = await asyncio.wait_for(complete_one(ch1, ch2, default=x), timeout=0.05)
    assert out == (x, 'default')

async def test_alts_wait_take():
    """
    WHEN
        No ready ports. A value put on channel while blocked.
    EXPECT
        Return (value, channel).
    """
    ch1 = create_channel()
    ch2 = create_channel()
    x = 'x'
    asyncio.get_running_loop().call_later(0.05, ch2.offer, x)
    out = await asyncio.wait_for(complete_one(ch1, ch2), timeout=0.1)
    assert out == (x, ch2)

async def test_alts_wait_put():
    """
    WHEN
        No ready ports.  A channel opens capacity while blocked.
    EXPECT
        Return (True, channel).
    """
    a = 'a'
    ch1 = create_channel()
    ch1.offer(a)
    b = 'b'
    ch2 = create_channel()
    ch2.offer(b)
    asyncio.get_running_loop().call_later(0.05, ch2.poll)
    c, d = 'c', 'd'
    out = await asyncio.wait_for(complete_one((ch1, c), (ch2, d)), timeout=0.1)
    assert out == (True, ch2)
    assert ch2.poll() == d

async def test_alts_multiple_ready_priority():
    """
    WHEN
        No ready ports and priority is True.  An operation becomes ready
        while blocked.
    EXPECT
        Return (value, channel).
    """
    ch1 = create_channel()
    ch2 = create_channel()
    x = 'x'
    def ready_both():
        ch1.offer(x)
        ch2.offer(x)
    asyncio.get_running_loop().call_later(0.05, ready_both)
    out = await asyncio.wait_for(complete_one(ch1, ch2, priority=True), timeout=0.1)
    assert out == (x, ch1)
    assert ch1.empty()
    assert not ch2.empty()

async def test_alts_multiple_ready_first_fails():
    """
    WHEN
        No ready ports and priority is True.  Multiple operations become
        ready while blocked, but the first ready channel is closed.
    EXPECT
        Return success and second channel.
    """
    a = 'a'
    ch1 = create_channel()
    ch1.offer(a)
    b = 'b'
    ch2 = create_channel()
    ch2.offer(b)
    def ready_both_close_ch1():
        ch1.poll()
        ch1.close()
        ch2.poll()
    asyncio.get_running_loop().call_later(0.05, ready_both_close_ch1)
    c, d = 'c', 'd'
    out = await asyncio.wait_for(
        complete_one((ch1, c), (ch2, d), priority=True),
        timeout=0.1)
    assert out == (True, ch2)
    assert ch1.empty()
    assert ch2.poll() == d

async def test_alts_take_from_shielded_channel():
    """
    WHEN
        A take operation on a channel wrapped in a shield (a readable
        channel that is not a Channel instance).
    EXPECT
        The take completes; the shield is not mistaken for a put tuple.
    """
    ch = create_channel()
    shielded = shield_from_close(ch)
    ch.offer('x')
    out = await asyncio.wait_for(complete_one(shielded), timeout=0.5)
    assert out == ('x', shielded)

async def test_alts_put_unhashable_value_retry():
    """
    WHEN
        Put operations carry unhashable values and the first ready
        channel fails (closed), forcing the retry path.
    EXPECT
        No TypeError from hashing ch_ops; the put completes on the
        remaining channel.
    """
    a = create_channel()
    a.offer('a')
    b = create_channel()
    b.offer('b')
    def free_and_close_a():
        a.poll()
        a.close()
    asyncio.get_running_loop().call_later(0.05, free_and_close_a)
    asyncio.get_running_loop().call_later(0.1, b.poll)
    va = {'k': 'a'}
    vb = {'k': 'b'}
    out = await asyncio.wait_for(complete_one((a, va), (b, vb)), timeout=0.5)
    assert out == (True, b)
    assert b.poll() == vb

async def test_alts_priority_order_preserved_after_retry():
    """
    WHEN
        priority is True, the first channel becomes a dud (closed
        empty), and the remaining channels later become ready together.
    EXPECT
        The operation completes on the earliest remaining channel in
        the original argument order.
    """
    chs = [create_channel() for _ in range(4)]
    def ready_rest():
        for ch, x in zip(chs[1:], 'bcd'):
            ch.offer(x)
    asyncio.get_running_loop().call_later(0.05, chs[0].close)
    asyncio.get_running_loop().call_later(0.1, ready_rest)
    out = await asyncio.wait_for(
        complete_one(*chs, priority=True), timeout=0.5)
    assert out == ('b', chs[1])

async def test_alts_zero_ch_ops():
    """
    WHEN
        complete_one is called with no ch_ops.
    EXPECT
        Returns (None, None) immediately.
    """
    out = await asyncio.wait_for(complete_one(), timeout=0.1)
    assert out == (None, None)

async def test_alts_all_closed():
    """
    WHEN
        Every channel passed to complete_one is already closed and empty.
    EXPECT
        Returns (None, None) without blocking.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    ch1.close()
    ch2.close()
    out = await asyncio.wait_for(complete_one(ch1, ch2), timeout=0.5)
    assert out == (None, None)

async def test_alts_multiple_ready_first_batch_fails():
    """
    WHEN
        No ready ports.  Multiple operations become ready while blocked
        but first batch of channels are closed. Later another batch of
        channels become ready.
    EXPECT
        Return success and fourth channel.
    """
    a = 'a'
    ch1 = create_channel()
    ch1.offer(a)
    b = 'b'
    ch2 = create_channel()
    ch2.offer(b)
    def ready_and_close_both():
        ch1.poll()
        ch1.close()
        ch2.poll()
        ch2.close()
    c = 'c'
    ch3 = create_channel()
    ch3.offer(c)
    d = 'd'
    ch4 = create_channel()
    ch4.offer(d)
    def ready_and_close_ch3():
        ch3.poll()
        ch3.close()
        ch4.poll()
    asyncio.get_running_loop().call_later(0.05, ready_and_close_both)
    asyncio.get_running_loop().call_later(0.1, ready_and_close_ch3)
    e, f, g, h = 'e', 'f', 'g', 'h'
    out = await asyncio.wait_for(
        complete_one((ch1, e), (ch2, f), (ch3, g), (ch4, h)),
        timeout=0.15)
    assert out == (True, ch4)
    assert ch1.empty()
    assert ch2.empty()
    assert ch3.empty()
    assert ch4.poll() == h
