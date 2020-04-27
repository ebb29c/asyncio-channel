from asyncio_channel._dropping_queue import DroppingQueue

import asyncio
import pytest


def test_put_nowait():
    """
    GIVEN
        Queue is not full.
    WHEN
        Put an item.
    EXPECT
        Item is added.
    """
    q = asyncio.Queue(1)
    db = DroppingQueue(q)
    a = 'a'
    db.put_nowait(a)
    assert db.get_nowait() == a

def test_put_nowait_full():
    """
    GIVEN
        Queue is full.
    WHEN
        Put an item.
    EXPECT
        Item is added.
    """
    q = asyncio.Queue(1)
    db = DroppingQueue(q)
    a = 'a'
    db.put_nowait(a)
    b = 'b'
    db.put_nowait(b)
    assert db.get_nowait() == a

@pytest.mark.asyncio
async def test_put():
    """
    GIVEN
        Queue is not full.
    WHEN
        Put an item.
    EXPECT
        Item is added.
    """
    q = asyncio.Queue(1)
    db = DroppingQueue(q)
    a = 'a'
    await asyncio.wait_for(db.put(a), timeout=0.05)
    assert db.get_nowait() == a

@pytest.mark.asyncio
async def test_put_full():
    """
    GIVEN
        Queue is full.
    WHEN
        Put an item.
    EXPECT
        Item is added.
    """
    q = asyncio.Queue(1)
    db = DroppingQueue(q)
    a = 'a'
    await asyncio.wait_for(db.put(a), timeout=0.05)
    b = 'b'
    await asyncio.wait_for(db.put(b), timeout=0.05)
    assert db.get_nowait() == a
