from asyncio_channel._channel import Channel

import asyncio
import pytest


def test_constructor():
    """
    WHEN
        Channel is constructed.
    EXPECT
        It is not closed.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    assert not ch.is_closed()

def test_close():
    """
    GIVEN
        Channel is open.
    WHEN
        close() is called on a Channel.
    EXPECT
        It is closed.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    ch.close()
    assert ch.is_closed()

@pytest.mark.asyncio
async def test_closed():
    """
    GIVEN
        Channel is open.
    WHEN
        Wait on closed.
    EXPECT
        Blocks.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(ch.closed(), timeout=0.05)

@pytest.mark.asyncio
async def test_closed_unblock():
    """
    GIVEN
        Channel is open.
    WHEN
        Wait on closed, and Channel is closed while blocked.
    EXPECT
        Unblocks.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    asyncio.get_running_loop().call_later(0.05, ch.close)
    await asyncio.wait_for(ch.closed(), timeout=0.1)

def test_offer():
    """
    GIVEN
        Channel is not full.
    WHEN
        Offered an item.
    EXPECT
        The item is added to the queue and offer returns True.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    x = 'x'
    assert ch.offer(x)
    assert q.qsize() == 1
    assert q.get_nowait() == x

def test_offer_none():
    """
    GIVEN
        A channel.
    WHEN
        Offered None.
    EXPECT
        Raises ValueError.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    with pytest.raises(ValueError,
            match='None is not allowed on channel'):
        ch.offer(None)

def test_offer_closed():
    """
    GIVEN
        Channel is closed.
    WHEN
        Offered an item.
    EXPECT
        The item is not added to the queue and offer returns False.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    ch.close()
    x = 'x'
    assert not ch.offer(x)
    assert q.empty()

def test_offer_full():
    """
    GIVEN
        Channel is full.
    WHEN
        Offered an item.
    EXPECT
        The item is not added to the queue and offer returns False.
    """
    a = 'a'
    q = asyncio.Queue(1)
    q.put_nowait(a)
    ch = Channel(q)
    b = 'b'
    assert not ch.offer(b)
    x = q.get_nowait()
    assert x != b

def test_poll():
    """
    GIVEN
        Channel is not empty.
    WHEN
        Polled for an item.
    EXPECT
        Returns the item.
    """
    x = 'x'
    q = asyncio.Queue()
    q.put_nowait(x)
    ch = Channel(q)
    assert ch.poll() == x

def test_poll_closed():
    """
    GIVEN
        Channel is closed but not empty.
    WHEN
        Polled for an item.
    EXPECT
        Returns an item.
    """
    x = 'x'
    q = asyncio.Queue()
    q.put_nowait(x)
    ch = Channel(q)
    ch.close()
    assert ch.poll() == x

def test_poll_empty():
    """
    GIVEN
        Channel is empty.
    WHEN
        Polled for an item.
    EXPECT
        Returns None
    """
    q = asyncio.Queue()
    ch = Channel(q)
    assert ch.poll() is None

def test_poll_empty_given_value():
    """
    GIVEN
        Channel is empty.
    WHEN
        Polled for an item, and a default value is given.
    EXPECT
        Returns the given default value.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    x = 'x'
    assert ch.poll(default=x) == x

@pytest.mark.asyncio
async def test_put():
    """
    GIVEN
        Channel is open and not full.
    WHEN
        Put an item.
    EXPECT
        Item is added to the Channel and returns True.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    x = 'x'
    assert await asyncio.wait_for(ch.put(x), timeout=0.05)
    assert q.get_nowait() == x

@pytest.mark.asyncio
async def test_put_closed():
    """
    GIVEN
        Closed Channel.
    WHEN
        Put an item.
    EXPECT
        Item is not added to the Channel and returns False.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    ch.close()
    x = 'x'
    result = await asyncio.wait_for(ch.put(x), timeout=0.05)
    assert result == False
    assert q.empty()

@pytest.mark.asyncio
async def test_put_full():
    """
    GIVEN
        Channel is open and full.
    WHEN
        Put an item.
    EXPECT
        Put blocks.
    """
    a = 'a'
    q = asyncio.Queue(1)
    q.put_nowait(a)
    ch = Channel(q)
    b = 'b'
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(ch.put(b), timeout=0.05)
    assert q.get_nowait() == a

@pytest.mark.asyncio
async def test_put_full_unblock():
    """
    GIVEN
        Channe is open and full.
    WHEN
        Put and item, and an item is taken while blocked.
    EXPECT
        Item is added to Channel and returns True.
    """
    a = 'a'
    q = asyncio.Queue(1)
    q.put_nowait(a)
    ch = Channel(q)
    asyncio.get_running_loop().call_later(0.05, ch.poll)
    b = 'b'
    assert await asyncio.wait_for(ch.put(b), timeout=0.1)
    assert q.get_nowait() == b

@pytest.mark.asyncio
async def test_put_full_timeout():
    """
    GIVEN
        Channel is open and full.
    WHEN
        Put an item and a timeout is given.
    EXPECT
        Item is not added to Channel and returns False.
    """
    a = 'a'
    q = asyncio.Queue(1)
    q.put_nowait(a)
    ch = Channel(q)
    b = 'b'
    assert not await ch.put(b, timeout=0.05)
    assert q.get_nowait() == a

@pytest.mark.asyncio
async def test_put_full_close():
    """
    GIVEN
        Channel is open and full.
    WHEN
        Put an item.  While blocked, the Channel is closed.
    EXPECT
        Item is not added to Channel and returns False.
    """
    a = 'a'
    q = asyncio.Queue(1)
    q.put_nowait(a)
    ch = Channel(q)
    asyncio.get_running_loop().call_later(0.05, ch.close)
    b = 'b'
    assert not await asyncio.wait_for(ch.put(b), timeout=0.1)
    assert q.get_nowait() == a

@pytest.mark.asyncio
async def test_take():
    """
    GIVEN
        Channel is open and not empty.
    WHEN
        Take an item.
    EXPECT
        Returns first item added to the Channel.
    """
    a = 'a'
    b = 'b'
    q = asyncio.Queue()
    q.put_nowait(a)
    q.put_nowait(b)
    ch = Channel(q)
    result = await asyncio.wait_for(ch.take(), timeout=0.05)
    assert result == a

@pytest.mark.asyncio
async def test_take_closed():
    """
    GIVEN
        Channel is closed.
    WHEN
        Take an item.
    EXPECT
        Returns None.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    ch.close()
    result = await asyncio.wait_for(ch.take(), timeout=0.05)
    assert result is None

@pytest.mark.asyncio
async def test_take_closed_default():
    """
    GIVEN
        Channel is closed.
    WHEN
        Take an item, and default value is given.
    EXPECT
        Returns the given default value.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    ch.close()
    x = 'x'
    result = await asyncio.wait_for(ch.take(default=x), timeout=0.05)
    assert result == x

@pytest.mark.asyncio
async def test_take_empty():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Get an item.
    EXPECT
        Get blocks.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(ch.take(), timeout=0.05)

@pytest.mark.asyncio
async def test_take_unblock():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Get an item, and an item is added while blocked.
    EXPECT
        Returns the added item.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    x = 'x'
    asyncio.get_running_loop().call_later(0.05, ch.offer, x)
    result = await asyncio.wait_for(ch.take(), timeout=0.1)
    assert result == x

@pytest.mark.asyncio
async def test_take_empty_close_default():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Get an item, a default value is given, and the Channel is closed
        while blocked.
    EXPECT
        Returns given default value.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    asyncio.get_running_loop().call_later(0.05, ch.close)
    x = 'x'
    result = await asyncio.wait_for(ch.take(default=x), timeout=0.1)
    assert result == x

@pytest.mark.asyncio
async def test_take_empty_timeout():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Get an item and a timeout is given.
    EXPECT
        Returns None.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    assert await ch.take(timeout=0.05) is None

@pytest.mark.asyncio
async def test_take_empty_timeout_default():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Get an item, a timeout and defautl value are given.
    EXPECT
        Returns given default value.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    x = 'x'
    assert await ch.take(timeout=0.05, default=x) == x

@pytest.mark.asyncio
async def test_capacity():
    """
    GIVEN
        Channel is open and full.
    WHEN
        Wait for capacity.
    EXPECT
        Blocks.
    """
    q = asyncio.Queue(1)
    ch = Channel(q)
    x = 'x'
    ch.offer(x)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(ch.capacity(), timeout=0.05)

@pytest.mark.asyncio
async def test_capacity_unblock():
    """
    GIVEN
        Channel is open and full.
    WHEN
        Wait for capacity, and an item is take while blocked.
    EXPECT
        Unblocks and returns True.
    """
    q = asyncio.Queue(1)
    ch = Channel(q)
    x = 'x'
    ch.offer(x)
    asyncio.get_running_loop().call_later(0.05, ch.poll)
    assert await ch.capacity(timeout=0.1)
    assert ch.offer(x)

@pytest.mark.asyncio
async def test_capacity_timeout_unblock():
    """
    GIVEN
        Channel is open and full.
    WHEN
        Wait for capacity, and timeout elapses.
    EXPECT
        Unblocks and returns True.
    """
    q = asyncio.Queue(1)
    ch = Channel(q)
    ch.offer('x')
    assert not await ch.capacity(timeout=0.1)
    assert ch.full()

@pytest.mark.asyncio
async def test_capacity_close_unblock():
    """
    GIVEN
        Channel is open and full.
    WHEN
        Wait for capacity, and close channel.
    EXPECT
        Unblocks and returns False.
    """
    q = asyncio.Queue(1)
    ch = Channel(q)
    ch.close()
    assert not await ch.capacity(timeout=0.05)
    assert not ch.offer('x')

@pytest.mark.asyncio
async def test_capacity_unblock_next():
    """
    GIVEN
        Channel is open and full, and two coroutines are awaiting
        capacity.
    WHEN
        Capacity becomes available, and first unblocked coroutine does
        not put item.
    EXPECT
        Second coroutine unblocks.
    """
    q = asyncio.Queue(1)
    ch = Channel(q)
    assert ch.offer('a')
    asyncio.get_running_loop().call_later(0.05, ch.poll)
    await asyncio.wait_for(
        asyncio.gather(ch.capacity(), ch.capacity()),
        timeout=0.1)

@pytest.mark.asyncio
async def test_capacity_next_reblocks():
    """
    GIVEN
        Channel is open and full, and two coroutines are awaiting
        capacity.
    WHEN
        Capacity becomes available, and first unblocked coroutine
        puts an item.
    EXPECT
        Second coroutine remains blocked.
    """
    q = asyncio.Queue(1)
    ch = Channel(q)
    assert ch.offer('a')
    b = 'b'
    async def put_item():
        await ch.capacity()
        ch.offer(b)
    asyncio.get_running_loop().call_later(0.05, ch.poll)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            asyncio.gather(put_item(), ch.capacity()),
            timeout=0.1)
    # Verify that new item was put and unblock the second coroutine.
    assert await ch.take() == b

@pytest.mark.asyncio
async def test_item():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Wait for item.
    EXPECT
        Blocks.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(ch.item(), timeout=0.05)

@pytest.mark.asyncio
async def test_item_unblock():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Wait for item, and item is added while blocked.
    EXPECT
        Unblocks and returns True.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    x = 'x'
    asyncio.get_running_loop().call_later(0.05, ch.offer, x)
    assert await ch.item(timeout=0.1)
    assert ch.poll() == x

@pytest.mark.asyncio
async def test_item_timeout_unblock():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Wait for item, and timeout elapses.
    EXPECT
        Unblocks and returns False.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    assert not await ch.item(timeout=0.05)
    assert ch.empty()

@pytest.mark.asyncio
async def test_item_close_unblock():
    """
    GIVEN
        Channel is open and empty.
    WHEN
        Wait for item, and close channel.
    EXPECT
        Unblocks and returns False.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    asyncio.get_running_loop().call_later(0.05, ch.close)
    assert not await ch.item(timeout=0.1)
    assert ch.empty()

@pytest.mark.asyncio
async def test_item_unblock_next():
    """
    GIVEN
        Channel is open and empty, and two coroutines are awaiting
        an item.
    WHEN
        An item becomes available, and first unblocked coroutine does
        not take it.
    EXPECT
        Second coroutine unblocks.
    """
    q = asyncio.Queue(1)
    ch = Channel(q)
    asyncio.get_running_loop().call_later(0.05, ch.offer, 'a')
    await asyncio.wait_for(
        asyncio.gather(ch.item(), ch.item()),
        timeout=0.1)

@pytest.mark.asyncio
async def test_item_next_reblocks():
    """
    GIVEN
        Channel is open and empty, and two coroutines are awaiting
        an item.
    WHEN
        An item becomes available, and first unblocked coroutine
        takes it.
    EXPECT
        Second coroutine remains blocked.
    """
    q = asyncio.Queue(1)
    ch = Channel(q)
    async def take_item():
        await ch.item()
        ch.poll()
    asyncio.get_running_loop().call_later(0.05, ch.offer, 'a')
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            asyncio.gather(take_item(), ch.item()),
            timeout=0.1)
    assert ch.empty()
    await ch.put('b')  # Unblock the second coroutine.

@pytest.mark.asyncio
async def test_aiter():
    """
    GIVEN
        Channel is open and not empty.
    WHEN
        Asynchronously iterate over the Channel, items will be
        added asynchronously, and then that Channel will be closed.
    EXPECT
        Items are read from the Channel in order and iteration
        stops when the Channel is closed.
    """
    q = asyncio.Queue()
    ch = Channel(q)
    delay = 0.025
    xs = ['a', 'b', 'c', 'd']
    call_later = asyncio.get_running_loop().call_later
    for x in xs:
        call_later(delay, ch.offer, x)
        delay += 0.025
    call_later(delay, ch.close)
    buf = []
    async for x in ch:
        buf.append(x)
    assert buf == xs
