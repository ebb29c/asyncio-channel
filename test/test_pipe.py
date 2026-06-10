from asyncio_channel import create_channel
from asyncio_channel._pipe import pipe

import asyncio
import pytest


async def test_pipe_close_false():
    """
    GIVEN
        close argument is False.
    WHEN
        src channel closes.
    EXPECT
        dest channel to remain open.
    """
    src = create_channel()
    dest = create_channel()
    pipe(src, dest, close=False)
    asyncio.get_running_loop().call_later(0.01, src.close)
    await asyncio.wait_for(src.closed(), timeout=1.0)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(dest.closed(), timeout=1.0)

async def test_pipe_close_true():
    """
    GIVEN
        close argument is True.
    WHEN
        src channel closes.
    EXPECT
        dest channel to remain open.
    """
    src = create_channel()
    dest = create_channel()
    pipe(src, dest)
    asyncio.get_running_loop().call_later(0.01, src.close)
    await asyncio.wait_for(src.closed(), timeout=1.0)
    await asyncio.wait_for(dest.closed(), timeout=1.0)

async def test_pipe():
    """
    WHEN
        Item put to src channel.
    EXPECT
        Item is transfered to dest channel.
    """
    src = create_channel()
    dest = create_channel()
    pipe(src, dest)
    x = 'x'
    assert src.offer(x)
    assert await dest.take(timeout=0.05) == x
    assert src.empty()
    src.close()
    await asyncio.wait_for(dest.closed(), timeout=1.0)

async def test_pipe_no_item_loss_when_dest_refills():
    """
    GIVEN
        A pipe whose dest channel regained capacity, then was filled by
        another producer before src received an item.
    WHEN
        An item arrives on src.
    EXPECT
        The item is not lost; it is transferred once dest has capacity
        again.
    """
    src = create_channel()
    dest = create_channel()
    pipe(src, dest)
    # Let the pipe task enter its wait so dest.capacity() has already
    # completed (dest is empty at this point).
    for _ in range(5):
        await asyncio.sleep(0)
    # Fill dest from elsewhere, then satisfy the src.item() wait.
    assert dest.offer('blocker')
    assert src.offer('x')
    # Let the pipe task wake and run its loop body while dest is full.
    for _ in range(5):
        await asyncio.sleep(0)
    assert await dest.take(timeout=1.0) == 'blocker'
    # The polled item must not have been dropped on a failed offer.
    assert await dest.take(timeout=1.0) == 'x'
    src.close()
    await asyncio.wait_for(dest.closed(), timeout=1.0)

async def test_pipe_close():
    """
    GIVEN
        A non-empty and closed src.
    WHEN
        Pipe src to dest.
    EXPECT
        Item is transfered to dest channel.
    """
    src = create_channel()
    dest = create_channel()
    x = 'x'
    assert src.offer(x)
    src.close()
    pipe(src, dest)
    assert await dest.take(timeout=0.05) == x
    assert src.empty()
    await asyncio.wait_for(dest.closed(), timeout=1.0)
