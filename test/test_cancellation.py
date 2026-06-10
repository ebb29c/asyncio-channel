"""Tests for cancellation behaviour across the channel primitives."""

from asyncio_channel import complete_one, create_channel

import asyncio
import pytest


async def test_cancel_take():
    """
    GIVEN
        An empty channel.
    WHEN
        A take() coroutine is cancelled while blocked.
    EXPECT
        CancelledError is raised in the waiting coroutine.
    """
    ch = create_channel()
    task = asyncio.create_task(ch.take())
    await asyncio.sleep(0)  # Let task reach its first await.
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

async def test_cancel_put():
    """
    GIVEN
        A full channel.
    WHEN
        A put() coroutine is cancelled while blocked.
    EXPECT
        CancelledError is raised in the waiting coroutine.
    """
    ch = create_channel(1)
    ch.offer('existing')
    task = asyncio.create_task(ch.put('new'))
    await asyncio.sleep(0)  # Let task reach its first await.
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    # Original item must still be on the channel; new item was never added.
    assert ch.poll() == 'existing'
    assert ch.empty()

async def test_cancel_complete_one():
    """
    GIVEN
        An empty channel and a complete_one() call waiting for it.
    WHEN
        The complete_one coroutine is cancelled.
    EXPECT
        CancelledError is raised.
    """
    ch = create_channel()
    task = asyncio.create_task(complete_one(ch))
    await asyncio.sleep(0)  # Let task start waiting.
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
