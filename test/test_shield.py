from asyncio_channel import ProhibitedOperationError, create_channel, \
                            shield_from_close, shield_from_read, \
                            shield_from_write

import asyncio
import pytest


@pytest.mark.asyncio
async def test_shield_from_close_forwarding():
    """
    GIVEN
        An open channel, shielded from close.
    WHEN
        Call forwarded methods, i.e. everything except 'close'.
    EXPECT
        Normal channel behavior.
    """
    ch = create_channel()
    dch = shield_from_close(ch)
    assert dch.empty()
    assert not dch.full()
    a = 'a'
    assert dch.offer(a)
    assert not dch.empty()
    assert dch.full()
    assert dch.poll() == a
    b = 'b'
    assert await dch.put(b, timeout=0.05)
    assert await dch.take(timeout=0.05) == b
    asyncio.get_running_loop().call_later(0.05, dch.offer, a)
    assert await dch.item(timeout=0.1)
    asyncio.get_running_loop().call_later(0.05, dch.poll)
    assert await dch.capacity(timeout=0.1)
    assert not dch.is_closed()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(dch.closed(), timeout=0.05)
    asyncio.get_running_loop().call_later(0.05, ch.close)
    await asyncio.wait_for(dch.closed(), timeout=0.1)
    assert dch.is_closed()

@pytest.mark.asyncio
async def test_shield_from_read_forwarding():
    """
    GIVEN
        An open channel, shielded from read operations.
    WHEN
        Call forwarded methods, i.e. everything except 'item',
        'poll', and 'take'.
    EXPECT
        Normal channel behavior.
    """
    ch = create_channel()
    dch = shield_from_read(ch)
    assert dch.empty()
    assert not dch.full()
    a = 'a'
    assert dch.offer(a)
    assert not dch.empty()
    assert dch.full()
    assert ch.poll() == a
    b = 'b'
    assert await dch.put(b, timeout=0.05)
    assert await ch.take(timeout=0.05) == b
    assert ch
    asyncio.get_running_loop().call_later(0.05, ch.poll)
    assert await dch.capacity(timeout=0.1)
    assert not dch.is_closed()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(dch.closed(), timeout=0.05)
    asyncio.get_running_loop().call_later(0.05, dch.close)
    await asyncio.wait_for(dch.closed(), timeout=0.1)
    assert dch.is_closed()

@pytest.mark.asyncio
async def test_shield_from_write_forwarding():
    """
    GIVEN
        An open channel, shielded from write operations.
    WHEN
        Call forwarded methods, i.e. everything except 'capacity',
        'offer', and 'put'.
    EXPECT
        Normal channel behavior.
    """
    ch = create_channel()
    dch = shield_from_close(ch)
    assert dch.empty()
    assert not dch.full()
    a = 'a'
    assert ch.offer(a)
    assert not dch.empty()
    assert dch.full()
    assert dch.poll() == a
    b = 'b'
    assert await ch.put(b, timeout=0.05)
    assert await dch.take(timeout=0.05) == b
    asyncio.get_running_loop().call_later(0.05, ch.offer, a)
    assert await dch.item(timeout=0.1)
    assert not dch.is_closed()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(dch.closed(), timeout=0.05)
    asyncio.get_running_loop().call_later(0.05, ch.close)
    await asyncio.wait_for(dch.closed(), timeout=0.1)
    assert dch.is_closed()

def test_shield_from_close():
    """
    GIVEN
        An open channel, shielded from close.
    WHEN
        .close() is called.
    EXPECT
        Channel is not closed.
    """
    with pytest.raises(TypeError, match='must be a channel, not a int'):
        shield_from_close(1)
    ch = create_channel()
    dch = shield_from_close(ch, silent=True)
    dch.close()
    assert not ch.is_closed()
    dch = shield_from_close(ch)
    with pytest.raises(ProhibitedOperationError, match='close'):
        dch.close()

@pytest.mark.asyncio
async def test_shield_from_read():
    """
    GIVEN
        An open channel, shielded from read operations.
    WHEN
        Read operations ('item', 'poll', 'take') are called.
    EXPECT
        The operations return defaults or raise
        ProhibitedOperationError.
    """
    with pytest.raises(TypeError, match='must be a channel, not a int'):
        shield_from_read(1)
    ch = create_channel()
    dch = shield_from_read(ch, silent=True)
    assert not await dch.item()
    assert dch.poll() is None
    assert await dch.take() is None
    dch = shield_from_read(ch)
    with pytest.raises(ProhibitedOperationError, match='item'):
        await dch.item()
    with pytest.raises(ProhibitedOperationError, match='poll'):
        dch.poll()
    with pytest.raises(ProhibitedOperationError, match='take'):
        await dch.take()

@pytest.mark.asyncio
async def test_shield_from_write():
    """
    GIVEN
        An open channel, shielded from write operations.
    WHEN
        Write operations ('capacity', 'offer', 'put') are called.
    EXPECT
        The operations return defaults or raise
        ProhibitedOperationError.
    """
    with pytest.raises(TypeError, match='must be a channel, not a int'):
        shield_from_write(1)
    ch = create_channel()
    dch = shield_from_write(ch, silent=True)
    assert not await dch.capacity()
    assert not dch.offer('a')
    assert not await dch.put('b')
    dch = shield_from_write(ch)
    with pytest.raises(ProhibitedOperationError, match='capacity'):
        await dch.capacity()
    with pytest.raises(ProhibitedOperationError, match='offer'):
        dch.offer('a')
    with pytest.raises(ProhibitedOperationError, match='put'):
        await dch.put('b')

@pytest.mark.asyncio
async def test_shield_combined():
    """
    GIVEN
        An open channel, shielded from everything.
    WHEN
        Any operation is called.
    EXPECT
        The operation to return default or raise
        ProhibitedOperationError.
    """
    ch = create_channel()
    dch = shield_from_close(ch, silent=True)
    dch = shield_from_read(dch, silent=True)
    dch = shield_from_write(dch, silent=True)
    dch.close()
    assert not ch.is_closed()
    assert not await dch.item()
    assert dch.poll() is None
    assert await dch.take() is None
    assert not await dch.capacity()
    assert not dch.offer('a')
    assert not await dch.put('b')
    dch = shield_from_close(ch)
    dch = shield_from_read(dch)
    dch = shield_from_write(dch)
    with pytest.raises(ProhibitedOperationError, match='close'):
        dch.close()
    with pytest.raises(ProhibitedOperationError, match='item'):
        await dch.item()
    with pytest.raises(ProhibitedOperationError, match='poll'):
        dch.poll()
    with pytest.raises(ProhibitedOperationError, match='take'):
        await dch.take()
    with pytest.raises(ProhibitedOperationError, match='capacity'):
        await dch.capacity()
    with pytest.raises(ProhibitedOperationError, match='offer'):
        dch.offer('a')
    with pytest.raises(ProhibitedOperationError, match='put'):
        await dch.put('b')
