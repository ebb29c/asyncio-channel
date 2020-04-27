from asyncio_channel import create_channel
from asyncio_channel._pipe import pipe

import asyncio
import pytest


@pytest.mark.asyncio
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
    asyncio.get_running_loop().call_later(0.05, src.close)
    await asyncio.wait_for(src.closed(), timeout=0.05)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(dest.closed(), timeout=0.05)

@pytest.mark.asyncio
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
    asyncio.get_running_loop().call_later(0.05, src.close)
    await asyncio.wait_for(src.closed(), timeout=0.05)
    await asyncio.wait_for(dest.closed(), timeout=0.05)

@pytest.mark.asyncio
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
    await asyncio.wait_for(dest.closed(), timeout=0.05)

@pytest.mark.asyncio
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
    await asyncio.wait_for(dest.closed(), timeout=0.05)
