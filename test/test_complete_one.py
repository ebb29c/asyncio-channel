from asyncio_channel import complete_one, create_channel

import asyncio
import pytest


@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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
